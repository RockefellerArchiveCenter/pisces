

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
                #Find ref for the resource (this should be the same as the tree id)
                #Use that ref to grab the tree JSON
                #Store the tree data
                    #With tree data open
                    #GET CHILDREN & PARENTS
                    #USE THE TREE JSON to search for the object ID
                        #When you find the correct ID
                            #Check for children
                                #If you find children, store them to a list
                                #If you don't find children, don't do anything
                            #Go back up tree to find parents and ancestors
                                #Store them to a list
                #Check if object already exists in the database
