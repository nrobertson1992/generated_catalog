import time
import openai
import streamlit as st

openai.api_key = st.secrets['info']['openai_key']


# core messaging function.
def chatgpt(message,model='gpt-3.5-turbo'):
    while True:
        try:
            result = openai.ChatCompletion.create(
                      model=model,
                      messages=message)

            content = result['choices'][0]['message']['content']
            completion_tokens = result['usage']['completion_tokens']
            prompt_tokens = result['usage']['total_tokens']
            tokens = completion_tokens + prompt_tokens

            return content, tokens
        # Lazy exception error handling to back off and try the API again.
        except Exception as e:
            print(e)
            time.sleep(5)


def prompt_filter_job_df(user_input):
    return [{'role': 'system', 
             'content': f"""
             Which jobs in the list below are most relevant to the query. Return a Python list with the 
             relevant jobs,  like [job 1, job2, job3], where each job is a string. Sort in order of the most 
             relevant roles. Try to include 4-5 jobs. Limit to no more than 7 jobs. Just return the Python list, 
             no additional text.

            Query: {user_input}
            """
            }]

def prompt_filter_courses(jobs, course):
    return [{'role': 'system', 
             'content': f"""
             Does the course below feel like it teaches skills relevant to the list of jobs below?
             Feel free to be a little looser and include courses that you think could be relevant,
             even if not 100% sure.
             
            Jobs: 
            {jobs}
            
            Courses:
            {course}
            
            Desired Result format:
            Return either "True" or "False" as a string.
            """
            }]


def prompt_cluster_courses_label_generator(courses, user_input):
    return [{'role': 'system', 
             'content': f"""
             Given the original user input, create a 3-5 cluster names you think could be 
             used to cluster the courses. This should be written in a marketing tone, as this
             will be used to show a small curation of courses on an ecommerce website. The clusters
             should make sense with the original promt from the user.
            
            Original prompt:
            {user_input}
            
            Courses:
            {courses}
            
            Desired Result format: return the clusters you create in a Python list, formatted like below.
            No additional text is required. You do NOT need to return the course cluster assignments
[Cluster name 1, Cluster name 2, Cluster Name 3]
            """}]

def cluster_check(course, cluster):
    return [{'role': 'system', 
             'content': f"""
             Based on the course title, do you think this course belongs to the course cluster described below?
             Important: be strict, and only allow courses that you really think match this cluster.
             
             course: {course}
             cluster: {cluster}
            
            Desired Result format:
            Return either "True" or "False" as a string.
            """}]