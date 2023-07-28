# for time.sleep.
import time

# Data manipulation.
import pandas as pd
import numpy as np

# Progress tracking.
from tqdm import tqdm


# Multiprocessing
from multiprocessing.pool import ThreadPool as Pool

# For streamlit
import streamlit as st


# Fetch custom libraries!
import snowflake_queries as sq 
import chatgpt_prompts as gpt

# Cache.
@st.cache_data
def load_data():

	"""
	Fetch the following data:
	* taxonomy jobs.
	* taxonomy job-skill relationships.
	* taxonomy skill-course relationships.
	* course metadata.
	"""

	# Fetch data.
	data = []
	data_fetches = [sq.get_filtered_jobs_df, sq.get_job_skills, sq.get_course_skills, sq.get_course_metadata]
	progress_messages = ['Fetch job data', 'fetch job-skill relationships', 'fetch skill-course relationships','fetch course metadata']

	# Init progress bar.
	my_bar = st.progress(0, text="Fetching Data")

	# Handle progress bar tracking.
	for index in range(4):
		my_bar.progress((index+1)*25, text=progress_messages[index])
		data.append(data_fetches[index]())

	# Complete progress bar.
	my_bar.progress(100, text='Data loaded.')

	# Return the data from the list.
	return data[0], data[1], data[2], data[3]

@st.cache_data
def generate_recommendations(user_input, filtered_jobs_df, job_skills, course_skills, course_metadata):
	"""
	Generate a curated catalog tagged with cluster assignments.

	Inputs:
	* user_input: the prompt.
	* filtered_jobs_df: data from load_data().
	* job_skills: data from load_data().
	* course_skills: data from load_data().
	* course_metadata: data from load_data().

	Output:
	* Pandas dataframe of filtered courses.
	"""

	# Get list of jobs based on user prompt.
	my_bar = st.progress(0, text="🤖 Asking ChatGPT which Lightcast jobs feel relevant to your query.")
	prompt = gpt.prompt_filter_job_df(user_input=user_input)

	# Get content response.
	content, tokens = gpt.chatgpt(message=prompt)

	# Format jobs from content response.
	relevant_jobs = content.replace('\'','').replace('[','').replace(']','').replace('\n','').split(', ')

	@st.cache_data
	def get_relevant_courses(relevant_jobs):

		"""
		Get courses related to the jobs selected.

		Input:
		* relevant_jobs: Jobs found from the user_input.

		Output:
		* First draft of 
		"""
		
		job_ids = filtered_jobs_df[filtered_jobs_df['job_name'].isin(relevant_jobs)]['job_id']
		skill_ids = job_skills[job_skills['job_id'].isin(job_ids)]['skill_id']
		filtered_courses = course_skills[course_skills['skill_id'].isin(skill_ids)]['course_key']
		
		return course_metadata[course_metadata['course_key'].isin(filtered_courses)]

	my_bar.progress(20, text='📝 Translate Lightcast jobs into a course list')
	relevant_courses = get_relevant_courses(relevant_jobs)

	# Rank the courses to prune some of the candidates and save ChatGPT costs.
	@st.cache_data
	def intersection_ranker(relevant_jobs, relevant_courses):
		
		results = []
		
		job_id = filtered_jobs_df[filtered_jobs_df['job_name'].isin(relevant_jobs)]['job_id']
		skill_id = job_skills[job_skills['job_id'].isin(job_id)]['skill_id']
		job_skills_set = set(course_skills[course_skills['skill_id'].isin(skill_id)]['skill_name'].unique())
			
		for i, row in relevant_courses.iterrows():
			course_skills_set = set(row['skills'].split(', '))
			
			intersection = course_skills_set.intersection(job_skills_set)
			results.append(len(intersection) / len(job_skills_set))
			
		return results

	my_bar.progress(25, text='🔍 First phase course pruning: pick 200 curation candidates based on skill tags (intersection ratio).')

	relevant_courses['intersection_ranker'] = intersection_ranker(relevant_jobs, relevant_courses)


	# Add prompt for each course, and then do some more pruning to get to the 200 likely candidates.
	relevant_courses['prompt_base'] = 'level_type: ' + relevant_courses['level_type'] + ', course_title: ' + relevant_courses['course_title']
	relevant_courses['prompt_column'] = relevant_courses['course_title'].apply(lambda x: gpt.prompt_filter_courses(jobs=relevant_jobs, course=x))
	relevant_courses=relevant_courses[(relevant_courses['enrollment_count']>100) | (relevant_courses['course_product_line']=='Executive Education')]
	relevant_courses=relevant_courses.sort_values(by='intersection_ranker',ascending=False)[:200]

	# Ask ChatGPT to prune the 200 courses to courses it thinks are relevant to the original prompt.
	results = []
	tokens = 0


	my_bar.progress(35, text='🔍 Second phase course pruning by ChatGPT: select courses that look like they are related to the selected Lightcast jobs.')
	with Pool(8) as pool: # will Pool work when it is put on a server?

		for result in tqdm(pool.imap(gpt.chatgpt, relevant_courses['prompt_column'])):
			results.append(result[0])
			tokens += result[1]   
		
	pool.close()

	# Append results, filter.

	my_bar.progress(55, text='🗑️ Drop courses ChatGPT did not think were relevant')

	relevant_courses['relevant'] = results 
	relevant_courses=relevant_courses[relevant_courses['relevant']=='True']

	my_bar.progress(65, text='🤖 Ask ChatGPT to generate potential cluster names for remaining courses.')
	# Generate cluster titles. Use gpt-4 for this one to get better results!
	prompt = gpt.prompt_cluster_courses_label_generator(courses=relevant_courses['course_title'],user_input=user_input)
	content, tokens = gpt.chatgpt(message=prompt, model='gpt-4')

	generated_clusters = content.replace('[','').replace(']','').replace('\'','').replace('"','').split(', ')
	generated_clusters


	all_clusters = generated_clusters + ['For Executive Leaders', 'For Managers and High Potentials', 'For Individual Contributors']

	my_bar.progress(75, text='🤖 For each course, ask ChatGPT to decide which clusters it belongs in.')
	for cluster in all_clusters:
		
		relevant_courses['prompt_column'] = relevant_courses['course_title'].apply(
			lambda x: gpt.cluster_check(course=x, cluster=cluster))
		
		results = []
		tokens = 0

		with Pool(8) as pool:

			for result in tqdm(pool.imap(gpt.chatgpt, relevant_courses['prompt_column'])):
				results.append(result[0])
				tokens += result[1]   

		pool.close()
		
		relevant_courses[cluster] = results

	my_bar.progress(95, text="🧹 Cleaning Data.")
	relevant_courses = relevant_courses.drop(columns=['intersection_ranker', 'prompt_base', 'relevant', 'prompt_column'])

	my_bar.progress(100, text="🚀 Success! Results are loading now.")
	return relevant_courses, all_clusters

