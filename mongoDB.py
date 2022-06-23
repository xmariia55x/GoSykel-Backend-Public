import pymongo

client = pymongo.MongoClient("mongodb+srv://maria:maria@initialcluster.e1gh8.mongodb.net/GoSykel?retryWrites=true&w=majority&ssl=true&ssl_cert_reqs=CERT_NONE")
database = client.get_default_database()
user = database['User']
item = database['Item']
bycicle_lane = database['Bycicle_lane']
route = database['Route']
token = database['Token']

def disconnect_database():
    client.close()



