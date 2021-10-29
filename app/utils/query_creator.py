import config.constants as CONSTANTS
import traceback
import re

class QueryCreator():

    def row2dict(row):
        d = {}
        for column in row.__table__.columns:
            d[column.name] = str(getattr(row, column.name))
        return d

    def get_sql_query(resource, query_string):
        print(query_string)
        final_query = CONSTANTS.QUERY_PATTERN
        field_list = query_string.get('fields', CONSTANTS.DEFAULT_FIELD)
        limit_value = query_string.get('limit', CONSTANTS.PAGE_SIZE)
        offset_value = query_string.get('offset', CONSTANTS.DEFAULT_OFFSET)
        where_text  = ''

        if field_list != CONSTANTS.DEFAULT_FIELD:
            field_list = 'id,' + field_list
            query_string.pop('fields')
        
        if limit_value != CONSTANTS.PAGE_SIZE:
            query_string.pop('limit')

        if offset_value != CONSTANTS.DEFAULT_OFFSET:
            query_string.pop('offset')
        

        print("After [" + str(query_string) + "]")
        if query_string != {}:
            conditions = ''
            for key, values in query_string.items():
                current_str = key + '=' + "'" + str(values) + "',"
                conditions += current_str
            
            conditions = conditions[:-1]
            where_text = "where " + conditions
        print(where_text)
        final_query = re.sub(CONSTANTS.FIELD_IDENTIFIER, field_list, final_query)
        final_query = re.sub(CONSTANTS.TABLE_IDENTIFIER, resource, final_query)
        final_query = re.sub(CONSTANTS.WHERE_IDENTIFIER, where_text, final_query)
        final_query = re.sub(CONSTANTS.LIMIT_IDENTIFIER, limit_value, final_query)
        final_query = re.sub(CONSTANTS.OFFSET_IDENTIFIER, offset_value, final_query)
        return final_query


        


