import pandas as pd
import numpy as np
import streamlit as st

import snowflake.connector

# Returns a dataframe of data from edX's Snowflake.
def get_snowflake_data(query, columns):

    ctx = snowflake.connector.connect(
    user=st.secrets['DB_USERNAME'],
    password=st.secrets['DB_TOKEN'],
    account=st.secrets['info']['account'],
    warehouse=st.secrets['info']['warehouse'],
    database=st.secrets['info']['database'],
    role=st.secrets['info']['role'],
        )


    # Establish Snowflake cursor.
    cur = ctx.cursor()

    # Run the query.
    def run_query(query, columns):
        cur.execute(query)
        results = cur.fetchall()
        arr = np.array(results)
        df = pd.DataFrame(arr, columns=columns)
        return df

    df = run_query(query=query, columns=columns)

    # Return the dataframe.
    return df


def get_filtered_jobs_df():
	sql = st.secrets['info']['get_filtered_jobs_sql']

	cols = ['job_name', 'job_id','median_salary','# courses']

	df = get_snowflake_data(query=sql, columns=cols)
	df['job_id'] = df['job_id'].astype('int')

	return df


def get_job_skills():
	sql = st.secrets['info']['get_job_skills_sql']

	cols = ['job_id','skill_id']

	df = get_snowflake_data(query=sql, columns=cols)
	df['job_id'] = df['job_id'].astype('int')

	return df

def get_course_skills():

	sql = st.secrets['info']['get_course_skills_sql']
	cols = ['course_key','skill_id','skill_name']

	df = get_snowflake_data(query=sql, columns=cols)
	df['skill_id'] = df['skill_id'].astype('int')

	return df

def get_course_metadata():

	sql = st.secrets['info']['get_course_metadata_sql']

	cols = ['partner','course_key','course_title','level_type','course_product_line','url','image_link','is_enterprise_susbscription_course','enrollment_count','skills']

	df = get_snowflake_data(query=sql, columns=cols)

	return df


