

# Add data fetchers here

#LOGIC
#Get all archival objects updated in the last hour
    #For each updated archival object
        #Open and read the JSON
            #With JSON Open
                #Iterate through all linked agents and append their ids to a list
                    #Check to see if id exists in database
                        #if exists
                            #do nothing
                        #if doesn't exists
                            #get agent JSON based on its ID
                            #save JSON data for transformation and placement into DB
                #Iterate through all linked terms and append their ids to a list
                    #Check to see if id exists in database
                        #if exists
                            #do nothing
                        #if doesn't exists
                            #get term JSON based on its ID
                            #save JSON data for transformation and placement into DB
