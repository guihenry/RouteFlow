import pymongo as mongo
import bson
import redis

import rflib.ipc.IPC as IPC

FROM_FIELD = "from"
TO_FIELD = "to"
TYPE_FIELD = "type"
READ_FIELD = "read"
CONTENT_FIELD = "content"

# 1 MB for the capped collection
CC_SIZE = 1048576



def put_in_envelope(from_, to, msg):
    envelope = {}

    envelope[FROM_FIELD] = from_
    envelope[TO_FIELD] = to
    envelope[READ_FIELD] = False
    envelope[TYPE_FIELD] = msg.get_type()

    envelope[CONTENT_FIELD] = {}
    for (k, v) in msg.to_dict().items():
        envelope[CONTENT_FIELD][k] = v

    return envelope

def take_from_envelope(envelope, factory):
    msg = factory.build_for_type(envelope[TYPE_FIELD]);
    msg.from_dict(envelope[CONTENT_FIELD]);
    return msg;

def format_address(address):
    try:
        tmp = address.split(":")
        if len(tmp) == 2:
            return (tmp[0], int(tmp[1]))
        elif len(tmp) == 1:
            return (tmp[0],)
    except:
        raise ValueError, "Invalid address: " + str(address)
            
class MongoIPCMessageService(IPC.IPCMessageService):
    def __init__(self, address, db, id_, thread_constructor, sleep_function):
        """Construct an IPCMessageService

        Args:
            address: designates where the MongoDB instance is running.
            db: is the database name to connect to on MongoDB.
            id_: is an identifier to allow messages to be directed to the
                appropriate recipient.
            thread_constructor: function that takes 'target' and 'args'
                parameters for the function to run and arguments to pass, and
                return an object that has start() and join() functions.
            sleep_function: function that takes a float and delays processing
                for the specified period.
        """
        self._db = db
        self.address = format_address(address)
        self._id = id_
        self._producer_connection = mongo.Connection(*self.address)
        self._threading = thread_constructor
        self._sleep = sleep_function
  	
        arq = open('/home/routeflow/logs/MongoIPC.txt', 'w')
        arq.writelines("db: "+str(db)+"\n")
        arq.writelines("id: "+str(id_)+"\n")
        arq.writelines("address: "+str(address)+"\n")		
        arq.writelines("address formatado: "+str(self.address)+"\n")		
        arq.writelines("conections: "+str(self._producer_connection)+"\n")		
        arq.writelines("------------------------------------\n")		
		
        arq.close()
        #self.redis = redis.Redis('localhost')
		
        
    def listen(self, channel_id, factory, processor, block=True):
        worker = self._threading(target=self._listen_worker,
                                 args=(channel_id, factory, processor))
        worker.start()
        if block:
            worker.join()
        
    def send(self, channel_id, to, msg):
        #self._create_channel(self._producer_connection, channel_id)
        #collection = self._producer_connection[self._db][channel_id]
        #collection.insert(put_in_envelope(self.get_id(), to, msg))
		
        r = redis.Redis()
        r.publish(channel_id, msg)
		
		#metodo insert by Guilherme
        arq = open('/home/routeflow/logs/MongoIPC.txt', 'a')
		
        arq.writelines("channel_id: "+str(channel_id)+"\n")
        arq.writelines("self.get_id(): "+str(self.get_id())+"\n")		       
        arq.writelines("to: "+str(to)+"\n")
        arq.writelines("msg: "+str(msg)+"\n")			
        arq.writelines("------------------------------------\n")		
        arq.close()
		
        return True

    def _listen_worker(self, channel_id, factory, processor):
        connection = mongo.Connection(*self.address)
        self._create_channel(connection, channel_id)
        
        collection = connection[self._db][channel_id]
        cursor = collection.find({TO_FIELD: self.get_id(), READ_FIELD: False}, sort=[("_id", mongo.ASCENDING)])

        while True:
            for envelope in cursor:
                msg = take_from_envelope(envelope, factory)
                processor.process(envelope[FROM_FIELD], envelope[TO_FIELD], channel_id, msg);
                collection.update({"_id": envelope["_id"]}, {"$set": {READ_FIELD: True}})
				
				#metodo update by Guilherme
                #arq = open('/home/routeflow/logs/MongoIPC.txt', 'a')
                #arq.writelines("collection.update: "+str(collection)+"\n")     
                #arq.close()

            self._sleep(0.05)
            cursor = collection.find({TO_FIELD: self.get_id(), READ_FIELD: False}, sort=[("_id", mongo.ASCENDING)])
            
			#metodo find by Guilherme
            #arq = open('/home/routeflow/logs/MongoIPC.txt', 'a')
            #arq.writelines("collection.insert: "+str(collection)+"\n")        
            #arq.close()
                
    def _create_channel(self, connection, name):
        db = connection[self._db]
        try:
            collection = mongo.collection.Collection(db, name, None, True, capped=True, size=CC_SIZE)
            collection.ensure_index([("_id", mongo.ASCENDING)])
            collection.ensure_index([(TO_FIELD, mongo.ASCENDING)])
			
            #arq = open('/home/routeflow/logs/create_channel.txt', 'a')
            #arq.writelines("collection.ensure_index: "+str(collection)+"\n")        
            #arq.close()
        # TODO: improve this catch. It should be more specific, but pymongo
        # behavior doesn't match its documentation, so we are being dirty.
        except:
            pass

class MongoIPCMessage(dict, IPC.IPCMessage):
    def __init__(self, type_, **kwargs):
        dict.__init__(self)
        self.from_dict(kwargs)
        self._type = type_
        
    def get_type(self):
        return self._type

    def from_dict(self, data):
        for (k, v) in data.items():
            self[k] = v
        
    def from_bson(self, data):
        data = bson.BSON.decode(data)
        self.from_dict(data)

    def to_bson(self):
        return bson.BSON.encode(self)
        
    def str(self):
        string = ""
        for (k, v) in self.items():
            string += str(k) + ": " + str(v) + "\n"
        return string
        
    def __str__(self):
        return IPC.IPCMessage.__str__(self)
