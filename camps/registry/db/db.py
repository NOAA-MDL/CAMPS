import sys
import os
import sqlite3
import pdb
from collections import OrderedDict
import logging

from .. import util as cfg

try:
    db_name = os.environ['CAMPS_DB']
except KeyError:
    db_dir = os.path.expanduser('~')+'/.camps/'
    db_name = db_dir+'camps.db'
    # create the db directory if it does not exist
    if not os.path.isdir(db_dir):
        os.mkdir(db_dir)

def connect(db):
    """
    Returns sqlite3.Connection object for a given database
    housed in the db directory.
    """
    return sqlite3.connect(db, detect_types=sqlite3.PARSE_DECLTYPES)


conn = connect(db_name)
c = conn.cursor()

def create_file_id_table():
    """
    Creates a table in the database to keep track of processed
    files and file_id informaion.
    """
    table_name = 'file_info'
    conn = connect(db_name)
    c = conn.cursor()
    column_names_str = "(filename TEXT, file_id TEXT, PRIMARY KEY (filename, file_id))"
    sql = 'CREATE TABLE ' + table_name + ' ' + column_names_str
    try:
        c.execute(sql)
    except sqlite3.OperationalError:
        pass

def create_variable_db():
    """
    Creates a variable database based off of dictionary.
    Clears table if called.
    """
    table_name = 'variable'
    conn = connect(db_name)
    c = conn.cursor()
    #c.execute('DROP TABLE IF EXISTS ' + table_name)
    # Create the table
    fields = get_variable_ftypes().keys()
    types = get_variable_ftypes().values()

    column_names_str = "("
    for f, t in zip(fields, types):
        column_names_str += f
        column_names_str += " " + t + ", "
    column_names_str = column_names_str[0:-2] +  ", PRIMARY KEY (" +",".join(fields)+"))"
    sql = 'CREATE TABLE ' + table_name + ' ' + column_names_str
    try:
        c.execute(sql)
    except sqlite3.OperationalError:
        pass


def get_variable_ftypes():
    return OrderedDict([
       ('property', 'TEXT'),
       ('source', 'TEXT'),
       ('start', 'BIGINT'),
       ('end', 'BIGINT'),
       ('duration', 'BIGINT'),
       ('duration_method', 'TEXT'),
       ('vert_coord1', 'INTEGER'),
       ('vert_coord2', 'INTEGER'),
       ('vert_method', 'TEXT'),
       ('vert_units', 'TEXT'),
       ('filename', 'TEXT'),
       ('name', 'TEXT'),
       ('forecast_period', 'BIGINT'),
       ('file_id' , 'TEXT'),
       ('smooth' , 'INTEGER'),
       ('reserved1', 'TEXT'),
       ('reserved2', 'TEXT'),
       ('reserved3', 'TEXT')
        ])


def insert_variable(property=None, source=None, start=None, end=None,
                    duration=None, duration_method=None,
                    vert_coord1=None, vert_coord2=None, vert_method=None,
                    vert_units=None,
                    filename=None, name=None, forecast_period=None,
                    file_id=None, smooth=None,
                    reserved1=None, reserved2=None, reserved3=None):
    """Inserts variable metadata information into the table 'variable'.
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
    vert_units,
    filename,
    name,
    forecast_period,
    file_id,
    smooth,
    reserved1,
    reserved2,
    reserved3
    """
    table_name = 'variable'
    fields_string = ('?,' * len(get_variable_ftypes().keys()))[:-1]
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
        vert_units,
        filename,
        name,
        forecast_period,
        file_id,
        smooth,
        reserved1,
        reserved2,
        reserved3
]
    c.execute(sql, sql_values)
    conn.commit()

def insert_file_info(filename,file_id):
    """Insert file information into the file_info table
    """
    table_name = 'file_info'
    sql_str1 = "INSERT INTO " + table_name + " (filename, file_id) "
    sql_str2 = "VALUES ('" + filename + "', '" + file_id + "')"
    sql_str = sql_str1 + sql_str2
    sql_values = [filename, file_id]
    c.execute(sql_str)
    conn.commit()


def create_new_metadata_db():
    """Creates a metadata table in the database.
    This removes the existing metadata table.
    This is recreated at the start of every session importing CAMPS.
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
    try:
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
    except sqlite3.OperationalError:
        pass


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
    try:
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
    except sqlite3.OperationalError:
        pass

def get_file_info(filename,file_id):
    """queries the file_info table in the db to see if input file has already
    populated the db
    """
    db = 'file_info'
    where_str = 'file_id = "' + file_id + '"'
    sql_str = "SELECT DISTINCT * FROM " + db + " WHERE " + where_str
    c.execute(sql_str)
    finfo = c.fetchall()
    return finfo

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
    # If there is no vert method then has to be None to distinguish
    # between variables of same property with multi vert layers
    # We might want to expand this to loop over all possible kwargs
    # to be more explicit on what is None in the database query
    #if 'vert_method' not in kwargs:
    #    kwargs['vert_method'] = None
    # Construct a 'WHERE' string from kwargs
    where_str = ""
    for k,v in kwargs.iteritems():
        operator = "="
        if k == "start":
            operator = "<="
        elif k == "end":
            operator = ">="
        if v is None:
            where_str += k + " IS NULL" + " AND "
        else:
            where_str += k + " "+operator+" '" + str(v) + "' AND "
    where_str = where_str[0:-4] # Remove trailing 'AND'
    filename_index = name_arr.index('filename')
    name_index = name_arr.index('name')
    sql = "SELECT DISTINCT * FROM " + db + " WHERE " + where_str
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


def delete_variables_by_metadata(**kwargs):
    """
    Deletes variables matching given metadata.
    example: delete_variables_by_metadata(filename='brokenfile.nc')
    """
    db = 'variable'
    for k,v in kwargs.iteritems():
        sql = 'DELETE FROM ' + db + " WHERE " + k + "=" +"\""+v+"\""
        c.execute(sql)
        conn.commit()

def update_variables(column_name, match_value, update_column, value_change):
    """Updates value where key matches value"""
    db = 'variable'
    sql = "update "+db+" set "+update_column+" = '"+value_change+"' where "+column_name+" = '"+match_value+"'"
    c.execute(sql)
    conn.commit()

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
    try:
        index = name_arr.index(attr)
        sql = "SELECT " + attr + " FROM " + db + " WHERE name = '" + name + "'"
        c.execute(sql)
        return c.fetchone()[0]
    except ValueError as err:
        logging.error(attr + " is not a known metadata attribute")
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
    """Returns from the database table 'properties' the value
    of the attribute 'attr' for the variable 'name'.
    """

    db = 'properties'
    c.execute("PRAGMA table_info(" + db + ")")
    name_arr = c.fetchall()

    #Get attribute value of variable from database table 'properties'
    name_arr = [ele[1] for ele in name_arr] #Table column name at index 1
    try:
        sql = "SELECT " + attr + " FROM " + db + " WHERE name = '" + name + "'"
        c.execute(sql)
        property = c.fetchone()
        if property is not None:
            return property[0]
        return None

    except ValueError as err:
        logging.info(attr + " is not a known property attribute or " + name + " not defined")
        return False


def get_all_metadata(name):
    """Returns dictionary of attribute names and values
    that are defined for given variable name.
    """

    c.execute("PRAGMA table_info(metadata)")
    attr_names = c.fetchall()

    #Get all metadata stored in database table 'metadata' for variable 'name'
    attr_names = [ele[1] for ele in attr_names] #Table column name at index 1
    sql = "SELECT * FROM metadata WHERE name = '" + name + "'"
    c.execute(sql)
    attr_values = c.fetchone()

    #Cull the defined values before returning.
    defined_attr = {}
    if(attr_values is None):
        logging.warning(name + "not in metadata db")
        raise ValueError
        return False
    for key, val in zip(attr_names, attr_values):
        if val is not None and val != "":
            defined_attr[key] = val

    return defined_attr


def get_data_type(name):
    """Returns data_type stored in the database table 'properties'
    for this variable name.
    """

    return db.get_property(self.name, 'data_type')


#Same as get_data_type
def get_dimensions_type(name):
    """Returns data type of variable 'name'."""

    return db.get_property(self.name, 'data_type')


def print_properties(name):
    """Prints out the fields in database table 'properties' for
    variable 'name'."""

    db = "properties"
    print_from(db, name)


def print_metadata(name):
    """Prints out the fields in database table 'metadata' for
    variable 'name'."""

    db = "metadata"
    print_from(db, name)

def print_variable(name):
    """Prints out the fields in database table 'variable' for
    variable 'name'."""

    db = "variable"
    print_from(db, name)


def print_from(db, name):
    """Logs a formatted list of attribute names and their
    associated values in database table 'db' for variable 'name'.
    """

    #Obtain table 'db' column names
    c.execute("PRAGMA table_info(" + db + ")")
    name_arr = c.fetchall()
    name_arr = [ele[1] for ele in name_arr] #Table column name at index 1

    #Obtain the values in the fields of the table 'db' for variable 'name'
    #and log these values.
    sql = "SELECT * FROM " + db + " WHERE name = '" + name + "'"
    c.execute(sql)
    metadata = c.fetchone()
    if metadata == None:
        logging.info("No variable named "+name)
        return
    logging.info("Metadata for "+name)
    logging.info("%5s %1s %15s %1s %15s" % ('num',"|", db + ' name',"|", 'value'))
    logging.info("- - - - - - - - - - - - - - - - - - - - - - -")
    for i, value in enumerate(metadata):
        logging.info("%5d %1s %15s %1s %15s" % (i, "|", name_arr[i],"|", value))


def get_dictionary_attribute_keys(variables):
    """Gets all of the unique attribute names for each variable and
    returns an set of the results.
    """

    # if there's more that one data type for the same variable,
    # then use the least common denomenator. e.g. float are favored over ints

    # Add name manually
    all_attributes = {'name': str}
    for i in variables.values():
        try:
            attributes = i['attribute']
        except KeyError:
            logging.info("Keyword 'attribute' not in "+i)
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
    # then use the least common denomenator. e.g. ints are favored over floats
    all_properties = {'name': str}
    for i in variables.values():
        for name, value in i.iteritems():
            if name != 'attribute' and name != 'dimensions':
                if name in all_properties and all_properties[name] is int:
                    pass  # because we prefer integers
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
