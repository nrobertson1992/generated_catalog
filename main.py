import streamlit as st
import pandas as pd
import altair as alt

import generate_curation as gc

# Page title and input
st.title("Prototype: Curation with Generative AI")

filtered_jobs_df, job_skills, course_skills, course_metadata = gc.load_data()
st.toast('Data loaded: you can now provide instructions for the catalog you want built!', icon='🤖')

user_input = st.text_input("What would you like to search for? (provide a short descriptive query of the type of catalog you are building)",key='1283')


if user_input:

	df, all_clusters = gc.generate_recommendations(user_input, filtered_jobs_df, job_skills, course_skills, course_metadata)
	st.toast('Your curation is now ready!',icon='🎉')
	st.balloons()

	st.subheader('Curation Summary')


	# Create chart.
	st.markdown(f"""
		* Courses selected: {len(df)} ({len(df[df['course_product_line']=='OCM'])} OCM, {len(df[df['course_product_line']=='Executive Education'])} Exec Ed)
		* Clusters created: {len(all_clusters)}
		* Clusters: {all_clusters}""")


	visual = df[all_clusters + ['course_title']].melt('course_title', var_name='cluster', value_name='value')

	heatmap = alt.Chart(visual).mark_rect().encode(
		x='cluster',
		y='course_title',
		color=alt.Color('value', scale=alt.Scale(domain=['True', 'False'], range=['green', 'red'])),
		tooltip=['course_title','cluster','value']
		)

	st.altair_chart(heatmap, use_container_width=True)


	def convert_df(df):
			return df.to_csv().encode('utf-8')

	csv = convert_df(df)

	st.download_button(
			   "Download all Courses / Clusters in Curation",
			   csv,
			   "results.csv",
			   "text/csv",
			   key='download-csv'
				)

	st.subheader('Generated Clusters')

	st.write('Click one to see cluster')


	# Display carousel with Bootstrap cards
	for cluster in all_clusters:

		frame = df[df[cluster]=='True'].drop(columns=all_clusters)

		with st.expander(cluster):

			st.dataframe(data=frame)
			for i, row in frame.iterrows():

				col1, col2 = st.columns([1,3])

				with col1:
					st.image(row['image_link'], use_column_width=True)
				
				with col2:
					st.markdown(f'''**{row['course_title']}**''')
					st.write(f''' {row['course_product_line']} | {row['level_type']} | {row['partner']} | {row['course_key']}''')
					st.markdown(f'''*skills: {row['skills']}*''')

					st.write('''
								<head>
								<a target="_blank" href="{}">
									<button style="color:D23227;background-color:#FFFFFF";border-color:#D23227>
										See the course
									</button>
								</a>
								'''.format(row['url']),
								unsafe_allow_html=True)
				st.markdown('')
				st.markdown('')
				st.markdown('')





	st.subheader('All Courses')
	st.dataframe(data=df)

	st.download_button(
			   "Download all Courses / Clusters in Curation",
			   csv,
			   "results.csv",
			   "text/csv",
			   key='download-csv2'
				)
