import pandas as pd
from sqlalchemy import create_engine
import re


def get_db_connection():
    username = 'root'
    password = 'passwd'
    database_name = 'refactoring_analysis'
    server = '127.0.0.1'

    with open("../database.properties", 'r') as db_file:
        for line in db_file:
            line = line.strip()
            username_search = re.search('^development.username=(.*)$', line, re.IGNORECASE)
            password_search = re.search('^development.password=(.*)$', line, re.IGNORECASE)
            url_search = re.search('^development.url=jdbc:mysql://(.*)/(.*)$', line, re.IGNORECASE)

            if username_search:
                username = username_search.group(1)
            if password_search:
                password = password_search.group(1)
            if url_search:
                server = url_search.group(1)
                database_name = url_search.group(2)

    return create_engine('mysql+pymysql://{}:{}@{}/{}'.format(username, password, server, database_name))


def regions_intersect(region_1_start, region_1_length, region_2_start, region_2_length):
    if region_1_start + region_1_length < region_2_start:
        return False
    elif region_2_start + region_2_length < region_1_start:
        return False
    return True


def record_involved(x):
    is_source = (x['type'] == 's' and
                 x['old_path'] == x['path'] and
                 regions_intersect(x['old_start_line'], x['old_length'], x['start_line'], x['length']))
    is_dest = (x['type'] == 'd' and
               x['new_path'] == x['path'] and
               regions_intersect(x['new_start_line'], x['new_length'], x['start_line'], x['length']))
    return is_source or is_dest


accepted_types = ['Change Package', 'Extract And Move Method', 'Extract Interface', 'Extract Method',
                      'Extract Superclass', 'Inline Method', 'Move And Rename Class', 'Move Attribute', 'Move Class',
                      'Move Method', 'Pull Up Attribute', 'Pull Up Method', 'Pull Up Method', 'Push Down Method',
                      'Rename Class', 'Rename Method']


def get_refactoring_types_sql_condition():
    type_condition = str()
    for ref_type in accepted_types:
        type_condition += 'refactoring_type = \"{}\" or '.format(ref_type)
    return type_condition[:-4]


def read_sql_table(table):
    print('Reading table {} from the database'.format(table))
    query = 'SELECT * FROM ' + table
    df = pd.read_sql(query, get_db_connection())
    return df


def get_merge_commits():
    return read_sql_table('merge_commit')


def get_conflicting_regions():
    return read_sql_table('conflicting_region')


def get_conflicting_region_histories():
    return read_sql_table('conflicting_region_history')


def get_refactorings():
    return read_sql_table('refactoring')


def get_accepted_refactorings():
    query = 'select * from refactoring where ({})'.format(get_refactoring_types_sql_condition())
    return pd.read_sql(query, get_db_connection())


def get_refactoring_regions():
    return read_sql_table('refactoring_region')


def get_accepted_refactoring_regions():
    print('Reading table refactoring_region from the database')

    query = 'select * from refactoring_region where refactoring_id in (select id from refactoring where ({}))'\
        .format(get_refactoring_types_sql_condition())
    return pd.read_sql(query, get_db_connection())


# output the number of ref types
def get_involved_refactorings_num_by_refactoring_type():
    conflicting_region_histories = get_conflicting_region_histories()
    refactorings = get_accepted_refactorings()
    refactoring_regions = get_accepted_refactoring_regions()

    involved_refs_count_per_project = pd.DataFrame()
    rr_grouped_by_project = refactoring_regions.groupby('project_id')
    counter = 0
    for project_id, project_crh in conflicting_region_histories.groupby('project_id'):
        counter += 1
        print('Processing project {}'.format(counter))
        if project_id not in rr_grouped_by_project.groups:
            continue
        project_rrs = rr_grouped_by_project.get_group(project_id)
        crh_rr_combined = pd.merge(project_crh.reset_index(), project_rrs.reset_index(), on='commit_hash', how='inner')
        involved_crh_rr = crh_rr_combined[crh_rr_combined.apply(record_involved, axis=1)]
        involved_refactorings = refactorings[refactorings['id'].isin(involved_crh_rr['refactoring_id'])]
        involved_ref_per_type = involved_refactorings.groupby('refactoring_type').id.nunique().to_frame().rename(
            columns={'id': 'involved_refs_count'})

        # for refactoring_index in involved_ref_per_type.index:
        #     if refactoring_index not in accepted_types:
        #         involved_ref_per_type = involved_ref_per_type.drop(refactoring_index)

        # involved_ref_per_type['involved_refs_count'] = involved_ref_per_type['involved_refs_count'] / sum(
        #     involved_ref_per_type['involved_refs_count'])
        involved_ref_per_type.rename(columns={'involved_refs_count': str(project_id)}, inplace=True)
        involved_refs_count_per_project = involved_refs_count_per_project.append(involved_ref_per_type.T)

    involved_refs_count_per_project.fillna(0).T.to_csv('results/involved_refactorings_num_by_refactoring_type.csv')
    return involved_refs_count_per_project.T

def get_overall_refactorings_num_by_refactoring_type():
    refactorings = get_accepted_refactorings()

    refactorings_count_per_project = pd.DataFrame()
    counter = 0
    for project_id, project_refactorings in refactorings.groupby('project_id'):
        counter += 1
        print('Processing project with id {}'.format(project_id))

        refactorings_per_type = project_refactorings.groupby('refactoring_type').id.nunique().to_frame().rename(
            columns={'id': 'refs_count'})

        # for refactoring_index in refactorings_per_type.index:
        #     if refactoring_index not in accepted_types:
        #         refactorings_per_type = refactorings_per_type.drop(refactoring_index)
        sum_num = sum(refactorings_per_type['refs_count'])
        # refactorings_per_type = refactorings_per_type.append({'refs_count': sum_num}, ignore_index=True)
        print('Sum num of refs of {} : {}'.format(project_id, sum_num))
        # refactorings_per_type['refs_count'] = refactorings_per_type['refs_count'] / sum(refactorings_per_type['refs_count'])
        refactorings_per_type.rename(columns={'refs_count': str(project_id)}, inplace=True)
        refactorings_count_per_project = refactorings_count_per_project.append(refactorings_per_type.T)

    refactorings_count_per_project.fillna(0).T.to_csv('results/overall_refactorings_num_by_refactoring_type2.csv')
    return refactorings_count_per_project.T
#


if __name__ == '__main__':
    # compute nums
    get_overall_refactorings_num_by_refactoring_type()
    # get_involved_refactorings_num_by_refactoring_type()