import sys
import os
relative_path = os.path.abspath(
    os.path.dirname(os.path.realpath(__file__)) + "/..")
sys.path.insert(0, relative_path)
import sqlite3
import util as cfg
import pdb

db_dir = os.path.dirname(os.path.realpath(__file__)) + '/'
db_name = 'wisps.db'


def connect(db):
    """
    Returns sqlite3.Connection object for a given database
    housed in the db directory.
    """
    return sqlite3.connect(db_dir + db, detect_types=sqlite3.PARSE_DECLTYPES)


conn = connect(db_name)
c = conn.cursor()


def create_variable_db():
    """
    Creates a variable database based off of dictionary
    """
    table_name = 'variable'
    conn = connect(db_name)
    c = conn.cursor()
    c.execute('DROP TABLE IF EXISTS ' + table_name)
    # Create the table
    fields = get_variable_fields()
    types = get_variable_types()
    column_names_str = "("
    for f, t in zip(fields, types):
        column_names_str += f
        column_names_str += " " + t + ", "
    column_names_str = column_names_str[0:-2] +  ", PRIMARY KEY (" +",".join(fields)+"))"
    print column_names_str
    sql = 'CREATE TABLE ' + table_name + ' ' + column_names_str
    c.execute(sql)


def get_variable_fields():
    return ['property', 'source', 'start', 'end',
            'duration', 'duration_method',
            'vert_coord1', 'vert_coord2', 'vert_method',
            'filename', 'name']


def get_variable_types():
    return ['TEXT', 'TEXT', 'BIGINT', 'BIGINT',
            'BIGINT', 'TEXT',
            'INTEGER', 'INTEGER', 'TEXT',
            'TEXT', 'TEXT']


def insert_variable(property, source, start, end,
                    duration, duration_method,
                    vert_coord1, vert_coord2, vert_method,
                    filename, name):
    """Inserts variable metadata information into the table. 
    Requires arguments in the following order:
    property, 
    source,
    start, 
    end, 
    duration, 
    duration_method, 
    vert_coord1, 
    vert_coord2, 
    vert_method, 
    filename,
    name
    """
    #var_db = 'variables.db'
    table_name = 'variable'
    fields_string = ('?,' * len(get_variable_fields()))[:-1]
    sql = "INSERT INTO " + table_name + " VALUES (" + fields_string + ")"
    sql_values = [
        property,
        source,
        start,
        end,
        duration,
        duration_method,
        vert_coord1,
        vert_coord2,
        vert_method,
        filename,
        name]
    c.execute(sql, sql_values)
    conn.commit()


def create_new_metadata_db():
    """
    Deletes old metadata table and replaces it with a new table 
    based on the configuration.
    """
    table_name = 'metadata'
    variables = cfg.read_variables()
    attr_names = get_dictionary_attribute_keys(variables)
    column_names_str = get_column_names_string(attr_names)
    conn = connect(db_name)
    c = conn.cursor()
    c.execute('DROP TABLE IF EXISTS ' + table_name)
    # Create the table
    sql = 'CREATE TABLE ' + table_name + ' ' + column_names_str
    c.execute(sql)
    # Fill the table
    fields_string = ('?,' * len(attr_names))[:-1]
    for name, values in variables.iteritems():
        sql = "INSERT INTO " + table_name + " VALUES (" + fields_string + ")"
        sql_values = []
        for attr_name in attr_names:
            if attr_name == 'name':
                sql_values.append(name)
            elif attr_name in values['attribute']:
                sql_values.append(values['attribute'][attr_name])
            else:
                sql_values.append(None)
        c.execute(sql, sql_values)

    conn.commit()


def create_new_properties_db():
    """
    Deletes old properties table and replaces it with a new table 
    based on the configuration.
    """
    table_name = 'properties'
    variables = cfg.read_variables()
    properties = get_dictionary_properties_keys(variables)
    column_names_str = get_column_names_string(properties)
    conn = connect(db_name)
    c = conn.cursor()
    c.execute('DROP TABLE IF EXISTS ' + table_name)
    # Create the table
    sql = 'CREATE TABLE ' + table_name + ' ' + column_names_str
    c.execute(sql)
    # Fill the table
    fields_string = ('?,' * len(properties))[:-1]
    for name, values in variables.iteritems():
        sql = "INSERT INTO " + table_name + " VALUES (" + fields_string + ")"
        sql_values = []
        for property_name in properties:
            if property_name == 'name':
                sql_values.append(name)
            elif property_name in values:
                sql_values.append(values[property_name])
            else:
                sql_values.append(None)
        c.execute(sql, sql_values)

    conn.commit()


def get_variable(**kwargs):
    """
    Returns the value of of the attribute for 
    the name.
    str name : name of predictor. e.g. wind_speed
    """
    db = 'variable'
    c.execute("PRAGMA table_info(" + db + ")")
    name_arr = c.fetchall()
    # The name of the column is at index 1. hence, ele[1]
    name_arr = [ele[1] for ele in name_arr]
    # Construct a 'WHERE' string from kwargs
    where_str = ""
    for k,v in kwargs.iteritems():
        where_str += k + " = '" + str(v) + "' AND "
    where_str = where_str[0:-4] # Remove 'AND'
    filename_index = name_arr.index('filename')
    name_index = name_arr.index('name')
    sql = "SELECT * FROM " + db + " WHERE " + where_str
    c.execute(sql)
    res = c.fetchall()
    for i,values in enumerate(res):
        res[i] = associate(name_arr, values)
    return res
    #if res:
    #    return (res[filename_index], res[name_index])

def associate(names, values):
    """Given a list of names and their associated values, 
    return a dictionary
    """
    return dict((x,y) for x, y in zip(names,values))

def get_all_variables(**kwargs):
    """
    Returns the value of of the attribute for 
    the name.
    str name : name of predictor. e.g. wind_speed
    """
    db = 'variable'
    c.execute("PRAGMA table_info(" + db + ")")
    name_arr = c.fetchall()
    # The name of the column is at index 1. hence, ele[1]
    name_arr = [ele[1] for ele in name_arr]
    # Construct a 'WHERE' string from kwargs
    where_str = ""
    for k,v in kwargs.iteritems():
        v = str(v)
        where_str += k + " = '" + v + "' AND "
    where_str = where_str[0:-4] # Remove 'AND'
    filename_index = name_arr.index('filename')
    name_index = name_arr.index('name')
    sql = "SELECT * FROM " + db + " WHERE " + where_str
    c.execute(sql)
    return c.fetchall()


def dump_db():
    db = 'variable'
    sql = 'SELECT * FROM ' + db
    c.execute(sql)
    return c.fetchall()



def get_metadata(name, attr):
    """
    Returns the value of of the attribute for 
    the name.
    str name : name of predictor. e.g. wind_speed
    """
    db = 'metadata'
    c.execute("PRAGMA table_info(" + db + ")")
    name_arr = c.fetchall()
    # The name of the column is at index 1. hence, ele[1]
    name_arr = [ele[1] for ele in name_arr]
    print name_arr
    try:
        index = name_arr.index(attr)
        sql = "SELECT " + attr + " FROM " + db + " WHERE name = '" + name + "'"
        c.execute(sql)
        return c.fetchone()[0]
    except ValueError as err:
        print attr + " is not a known metadata attribute"
        return False

def get_by_metadata(**kwargs):
    """
    Returns the value of of the attribute for 
    the name.
    str name : name of predictor. e.g. wind_speed
    """
    db = 'metadata'
    c.execute("PRAGMA table_info(" + db + ")")
    name_arr = c.fetchall()
    # The name of the column is at index 1. hence, ele[1]
    name_arr = [ele[1] for ele in name_arr]
    print name_arr
    # Construct a 'WHERE' string from kwargs
    where_str = ""
    for k,v in kwargs.iteritems():
        where_str += k + " = '" + v + "' AND "
    where_str = where_str[0:-4] # Remove 'AND'
    sql = "SELECT * FROM " + db + " WHERE " + where_str
    c.execute(sql)
    res = c.fetchone()
    if res:
        return res


def get_property(name, attr):
    """
    Returns the value of of the attribute for 
    the name.
    str name : name of predictor. e.g. wind_speed
    """
    db = 'properties'
    c.execute("PRAGMA table_info(" + db + ")")
    name_arr = c.fetchall()
    # The name of the column is at index 1. hence, ele[1]
    name_arr = [ele[1] for ele in name_arr]
    try:
        index = name_arr.index(attr)
        sql = "SELECT " + attr + " FROM " + db + " WHERE name = '" + name + "'"
        c.execute(sql)
        return c.fetchone()[0]
    except ValueError as err:
        print attr + " is not a known property attribute or " + name + " not defined"
        return False


def get_all_metadata(name):
    """
    Returns dictionary of attribute names and values 
    that are defined (not None or an empty string) for given variable name.
    str name : name of the variable.
    """
    defined_attr = {}
    #conn = connect(db_name)
    #c = conn.cursor()
    c.execute("PRAGMA table_info(metadata)")
    attr_names = c.fetchall()
    # The name of the column is at index 1. hence, ele[1]
    attr_names = [ele[1] for ele in attr_names]
    sql = "SELECT * FROM metadata WHERE name = '" + name + "'"
    c.execute(sql)
    attr_values = c.fetchone()
    if(attr_values is None):
        print name, "not in metadata db"
        raise ValueError
        return False
    for key, val in zip(attr_names, attr_values):
        if val is not None and val != "":
            defined_attr[key] = val
    return defined_attr


def get_data_type(name):
    """Check if data_type is defined in the properties
    database for this varibale name. Return value if available,
    otherwise throw ValueError.
    """
    return db.get_property(self.name, 'data_type')


def get_dimensions_type(name):
    """Check if dimensions is defined in the properties
    database for this varibale name. Return value if available,
    otherwise throw ValueError.
    """
    return db.get_property(self.name, 'data_type')


def print_properties(name):
    db = "properties"
    print_from(db, name)


def print_metadata(name):
    db = "metadata"
    print_from(db, name)


def print_from(db, name):
    """
    Prints a formatted list of attribute names and 
    their associated values for a given variable
    name.
    """
    #conn = connect(db_name)
    #c = conn.cursor()
    c.execute("PRAGMA table_info(" + db + ")")
    name_arr = c.fetchall()
    # The name of the column is at index 1. hence, ele[1]
    name_arr = [ele[1] for ele in name_arr]
    sql = "SELECT * FROM " + db + " WHERE name = '" + name + "'"
    c.execute(sql)
    metadata = c.fetchone()
    if metadata == None:
        print "No variable named " + name
        return
    print "Metadata for " + name
    print("%5s %15s %15s" % ('num', db + ' name', 'value'))
    print "- - - - - - - - - - - - - - - - - - - - - - -"
    for i, value in enumerate(metadata):
        print("%5d %15s %15s" % (i, name_arr[i], value))


def get_dictionary_attribute_keys(variables):
    """
    Gets all of the unique attribute names for each variable and
    returns an set of the results. 
    Parsing the config is specific to the nc_vars yaml file.
    """
    # if there's more that one data type for the same variable,
    # then use the least common denomenator. e.g. float are favored over ints

    # Add name manually
    all_attributes = {'name': str}
    for i in variables.values():
        try:
            attributes = i['attribute']
        except KeyError:
            print "keyword 'attribute' not in ", i
            raise
        for name, value in attributes.iteritems():
            if name in all_attributes and all_attributes[name] is float:
                pass  # to keep the float. Because we prefer floats.
            else:
                all_attributes[name] = type(value)

    return all_attributes


def get_dictionary_properties_keys(variables):
    """
    Gets all of the unique properties names for each variable and
    returns an set of the results. 
    Parsing the config is specific to the nc_vars yaml file.
    """
    # if there's more that one data type for the same variable,
    # then use the least common denomenator. e.g. float are favored over ints
    all_properties = {'name': str}
    for i in variables.values():
        for name, value in i.iteritems():
            if name != 'attribute' and name != 'dimensions':
                if name in all_properties and all_properties[name] is int:
                    pass  # because we prefer floats
                else:
                    all_properties[name] = type(value)

    return all_properties


def get_column_names_string(names):
    """
    returns a sqlite string for column names
    given a set of names. Assumes all columns are of type 'text'
    """
    db_names = "("
    for name, dtype in names.iteritems():
        if dtype is float:
            db_names = db_names + str(name) + " REAL, "
        elif dtype is int:
            db_names = db_names + str(name) + " INTEGER, "
        else:
            db_names = db_names + str(name) + " TEXT, "
    db_names = db_names[:-2] + ")"
    return db_names
