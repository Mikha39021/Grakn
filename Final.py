#!/usr/bin/env python
# coding: utf-8

# In[ ]:


from grakn.client import GraknClient
import csv


def build_phone_call_graph(inputs, data_path, keyspace_name):
    """
      gets the job done:
      1. creates a Grakn instance
      2. creates a session to the targeted keyspace
      3. for each input:
        - a. constructs the full path to the data file
        - b. loads csv to Grakn
      :param input as list of dictionaties: each dictionary contains details required to parse the data
    """
    with GraknClient(uri="localhost:48555") as client:  # 1
        with client.session(keyspace=keyspace_name) as session:  # 2
            for input in inputs:
                input["file"] = input["file"].replace(
                    data_path, "")  # for testing purposes
                input["file"] = data_path + input["file"]  # 3a
                print("Loading from [" + input["file"] +
                      ".csv] into Grakn ...")
                load_data_into_grakn(input, session)  # 3b


def load_data_into_grakn(input, session):
    """
      loads the csv data into our Grakn phone_calls keyspace:
      1. gets the data items as a list of dictionaries
      2. for each item dictionary
        a. creates a Grakn transaction
        b. constructs the corresponding Graql insert query
        c. runs the query
        d. commits the transaction
      :param input as dictionary: contains details required to parse the data
      :param session: off of which a transaction will be created
    """
    items = parse_data_to_dictionaries(input)  # 1

    for item in items:  # 2
        with session.transaction().write() as transaction:  # a
            graql_insert_query = input["template"](item)  # b
            print("Executing Graql Query: " + graql_insert_query)
            transaction.query(graql_insert_query)  # c
            transaction.commit()  # d

    print("\nInserted " + str(len(items)) +
          " items from [ " + input["file"] + ".csv] into Grakn.\n")


def company_template(company):
    graql_insert_query = 'insert $company isa company, has name "' + \
        company["name"] + '";'
    return graql_insert_query


def person_template(person):
    # insert person
    graql_insert_query = 'insert $person isa person, has phone-number "' + \
        person["phone-number"] + '"'

    # person is not a customer
    if (person["phone-number"].startswith("0930") == True) or (person["phone-number"].startswith("0912")):
        # person is not a customer
        graql_insert_query += ", has is-customer false"
    else:
        # person is a customer
        graql_insert_query += ", has is-customer true"
        graql_insert_query += ', has first-name "' + person["first-name"] + '"'
        graql_insert_query += ', has last-name "' + person["last-name"] + '"'
        graql_insert_query += ', has gender "' + person["gender"] + '"'
        graql_insert_query += ', has age "' + person["age"] + '"'
    graql_insert_query += ";"
    
    return graql_insert_query


def subscription_template(subscription):
    # match company
    graql_insert_query = 'match $company isa company, has name "' + \
        subscription["company_name"] + '";'
    # match person
    graql_insert_query += ' $customer isa person, has phone-number "' + \
        subscription["person_id"] + '";'
    # insert subscription
    graql_insert_query += (" insert $subscription(provider: $company, customer: $customer) isa subscription; " +
                           '$subscription has service_type "' + subscription["service_type"] + '";' +
                           '$subscription has date-started "' + subscription["date-started"]) + '";'
                           
    return graql_insert_query


def reward_template(reward):
    # match company
    graql_insert_query = ' match $company isa company, has name "' + \
        reward["company_name"] + '";'
    # match person
    graql_insert_query += ' $customer isa person, has phone-number "' + \
        reward["person_id"] + '";'
    # insert rewards type
    graql_insert_query += (" insert $reward(provider: $company, customer: $customer) isa reward; " +
                           "$reward has date-availed " + reward["date-availed"] + "; " +
                           "$reward has points_needed " + str(reward["points_needed"]) + "; " +
                           '$reward has description "' + reward["description"]) + '";'
    
    return graql_insert_query


def customer_address_template(customer_address):
    # insert customer_address
    graql_insert_query = 'insert $customer_address isa customer_address, has address_type "' + \
        customer_address["address_type"] + '"'
    graql_insert_query += ', has region "' + customer_address["region"] + '"'
    graql_insert_query += ', has street "' + customer_address["street"] + '"'
    graql_insert_query += ', has barangay "' + customer_address["barangay"] + '"'
    graql_insert_query += ', has town "' + customer_address["town"] + '"'
    graql_insert_query += ', has province "' + customer_address["province"] + '"'
    graql_insert_query += ";"

    return graql_insert_query

def cellsite_location_template(cellsite_location):
    # insert cellsite_location
    graql_insert_query = 'insert $cellsite_location isa cellsite_location, has cellsite-name "' + \
        cellsite_location["cellsite-name"] + '"'
    graql_insert_query += ', has CN-barangay "' + cellsite_location["CN-barangay"] + '"'
    graql_insert_query += ', has CN-town "' + cellsite_location["CN-town"] + '"'
    graql_insert_query += ', has CN-province "' + cellsite_location["CN-province"] + '"'
    graql_insert_query += ', has CN-region "' + cellsite_location["CN-region"] + '"'
    graql_insert_query += ";"

    return graql_insert_query

def call_template(call):
    # match caller
    graql_insert_query = 'match $caller isa person, has phone-number "' + \
        call["caller_id"] + '";'
    # match callee
    graql_insert_query += ' $callee isa person, has phone-number "' + \
        call["callee_id"] + '";'
    
    # match caller-residence
    graql_insert_query += ' $caller-residence isa customer_address, has address_id "' + \
        call["caller-residence"] + '";'
    if(["address_id"] != ""):
            graql_insert_query += ' $caller-residence isa customer_address, has address_id "' + '";'
   
    # match callee-residence
    graql_insert_query += ' $callee-residence isa customer_address, has address_id "' + \
        call["callee-residence"] + '";'
    if(["address_id"]!= ""):
            graql_insert_query += ' $callee-residence isa customer_address, has address_id "' + '";'
        
    # match caller-cellsite
    graql_insert_query += ' $caller-cellsite isa cellsite_location, has cellsite-name "' + \
        call["caller-cellsite-name"] + '";'
    if(["cellsite-name"] != ""):
            graql_insert_query += ' $caller-cellsite isa cellsite_location, has cellsite-name "' + '";'
    
     # match calleee-cellsite
    graql_insert_query += ' $calleee-cellsite isa cellsite_location, has cellsite-name "' + \
        call["callee-cellsite-name"] + '";'
    if(["cellsite-name"] != ""):
            graql_insert_query += ' $callee-cellsite isa cellsite_location, has cellsite-name "' + '";'
    
    # insert call
    graql_insert_query += (" insert $call(caller: $caller, caller-residence: $caller-residence, caller-cellsite: $caller-cellsite, callee: $callee, callee-residence: $callee-residence, callee-cellsite: $callee-cellsite) isa call; " +
                           "$call has started-at " + call["started_at"] + "; " +
                           "$call has duration " + str(call["duration"]) + ";")

    return graql_insert_query




def parse_data_to_dictionaries(input):
    items = []
    with open(input["file"] + ".csv") as data:  # 1
        for row in csv.DictReader(data, skipinitialspace=True):
            item = {key: value for key, value in row.items()}
            items.append(item)  # 2
    return items


Inputs = [
    {
        "file": "companies",
        "template": company_template
    },
    {
        "file": "people",
        "template": person_template
    },
    {
        "file": "subscriptions",
        "template": subscription_template
    },
    {
        "file": "rewards",
        "template": reward_template
    },
    {
        "file": "cellsite_locations",
        "template": cellsite_location_template
    },
    {
        "file": "customer_addresses",
        "template": customer_address_template
    },
    {
        "file": "calls",
        "template": call_template
    },

]

if __name__ == "__main__":
    build_phone_call_graph(inputs=Inputs, data_path=(
        "C:/Users/mikha.jane.d.mata/Desktop/FINAL TELECOM/data/"), keyspace_name="final_telecom")
