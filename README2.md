PROJECT: Explore Redis as Native Pub/Sub NoSQL DB  (datastructure-oriented) as alternative for MongoDB

Group 1:
Guilherme Henrique de Souza
Mauro Pereira de Jesus
Rogerio Adriano de Sousa


PROPOSITION:
The project aims at replacing the MongoDB database data bank data Redis, using the mechanism pub / sub.
The NoSQL databases do not use fixed schemas and joins, and store the data in the form of key / value or document format.
The database Redis stores its data in a hash table in which there is a single key and a pointer to a data or a particular item. The key-value model is the most simple and easy to implement, the increased interest in this type of database is to enable rapid inclusion and rapid consultation. This type of database does not have schemas.
MongoDB is a database-driven documents, and are similar to the key-value storage. The model is basically versioned documents that are collections of other collections of key-value. Documents are stored in JSON format, has a strong point of tolerance and incomplete as the main weakness in performance queries.


All the changes focused on MongoIPC.py file that is located within the RouteFlow \ rflib \ ipc. In this file were inserted several lines in order to understand its functioning within the RouteFlow, and was inserted into a line responsible for making the connection to the database Redis located on the current machine, and on the next line to include the information in the database data. Here we can see a snippet of code:

    def send(self, channel_id, to, msg):
        #self._create_channel(self._producer_connection, channel_id)
        #collection = self._producer_connection[self._db][channel_id]
        #collection.insert(put_in_envelope(self.get_id(), to, msg))
  	
        r = redis.Redis()
        r.publish(channel_id, msg)		
		
        return True
        
We can see that mechanism was used pub / sub Redis allows the insertion of a large amount of information through one channel, and the subsequent recovery of this information through the same channel. Since the main goal of this solution inclusion and rapid recovery of data.
