from typing import Any, Text, Dict, List
from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.events import AllSlotsReset,Restarted
import datetime
from rasa_sdk.events import SlotSet



# database connectivity

import mysql.connector

db_config = {
    "host": "127.0.0.1",
    "user": "root",
    "password": "root123",
    "database": "rasa_chatbot",
}

# Establish a connection to the database
conn = mysql.connector.connect(**db_config)

# connectivity finished

my_dict={}
class ActionAddItemToOrder(Action):
      def name(self):
            return "action_add_items_to_order"

      def run(self, dispatcher, tracker, domain):
       
      # how to run project
      # to activate virtual environment [ venv/Scripts/activate ]
      # step1 ->to run normat utter actions  [ rasa run -m models --enable-api --cors "*" ]
      # (if in any case if above server fails then we must make changes and rerun server)
      # step2 ->to run custom actions [ rasa run actions ]
      # (no need to  rerun server )
      # step3 ->run go live for index.html

            entities = tracker.latest_message['entities']
           
            store_entity_name=[]
            store_entity_value=[]

            if len(entities)!=0:
                  
                  
                  for ent in entities:
                        
                        if  ent["entity"]=="product" :
                              store_entity_name.append(ent["value"])
                        else :
                              store_entity_value.append(int(ent["value"]))
                    
                       
                  if len(store_entity_value)==len(store_entity_name):
                        for i in range(len(store_entity_name)):
                              my_dict.setdefault(store_entity_name[i], 0)
                              my_dict[store_entity_name[i]]+=store_entity_value[i]
                              # print(str(store_entity_value[i])+" "+ store_entity_name[i]+" added")

                        dispatcher.utter_message("और कुछ ")
                        

                  else :
                        store_entity_name.clear()
                        store_entity_value.clear()
                        dispatcher.utter_message("मैं समझ नहीं पाया कृपया व्यंजन(खाने का पदार्थ) और संख्या की जाँच करे")

            else:
                  
                  dispatcher.utter_message("No entities were mentioned in your message.")

            
            
            return []


class OrderCheckout(Action):
      def name(self):
            return "action_order_checkout"

      def run(self, dispatcher, tracker, domain):
      
 

            dispatcher.utter_message("ये रहा आपका आर्डर :\n")
            for key,value in my_dict.items():
                  dispatcher.utter_message(key+" "+str(value)+"\n")
            
            dispatcher.utter_message("आर्डर प्लेस करने के लिए हाँ लिखे अथवा [व्यंजन] [संख्या] कम करो या जोड़ दो लिखे \n")
            return []



class removeItemsFromOrder(Action):
      def name(self):
            return "action_remove_items_from_order"

      def run(self, dispatcher, tracker, domain):

            entities = tracker.latest_message['entities']
           
            store_entity_name=[]
            store_entity_value=[]

            if len(entities)!=0:
                  
                  
                  for ent in entities:
                        
                        if  ent["entity"]=="product" :
                              store_entity_name.append(ent["value"])
                        else :
                              store_entity_value.append(int(ent["value"]))
                    
                       
                  cnt=0
                  remove=0
                  if len(store_entity_value)==len(store_entity_name):
                        for i in range(len(store_entity_name)):
                              
                              
                              if(store_entity_value[i] <= my_dict[store_entity_name[i]]):
                                    my_dict[store_entity_name[i]]-=store_entity_value[i]

                                    if(my_dict[store_entity_name[i]]==0):
                                          my_dict.pop(store_entity_name[i])
                                          
                                    dispatcher.utter_message(str(store_entity_value[i])+" "+store_entity_name[i]+" निकाले गए"+"\n")
                                    
                              else:
                                    cnt=1
                                    remove=my_dict[store_entity_name[i]]
                                    break

                        if cnt==1:
                              dispatcher.utter_message("माफ़ कीजिये गा पर आप" +str(remove)+ "से ज्यादा नहीं निकाल सकते \n")
                        
                        else: 
                              
                              dispatcher.utter_message("और कुछ ")
                        
                        

                  else :
                        store_entity_name.clear()
                        store_entity_value.clear()
                        dispatcher.utter_message("मैं समझ नहीं पाया कृपया व्यंजन(खाने का पदार्थ) और संख्या की जाँच करे \n")
            else:
                  dispatcher.utter_message("मैं समझ नहीं पाया कृपया व्यंजन(खाने का पदार्थ) और संख्या की जाँच करे \n")
                 
            
            return []




class OrderFinish(Action):
      def name(self):
            return "action_order_finish"

      def run(self, dispatcher, tracker, domain):
      
            if len(my_dict)==0:
                  dispatcher.utter_message("माफ़ कीजियेगा पर बिना कुछ आर्डर किये आप आर्डर प्लेस नहीं कर सकते")
                  return []

            cursor = conn.cursor()
            query="SELECT MAX(order_id) FROM orders"
            cursor.execute(query)
            newOrderId = cursor.fetchone()[0]
            newOrderId+=1    #start the new order

       
            for key,value in my_dict.items():
                  
                  quantity=value
                  
                  query1 = "SELECT item_id FROM food_items WHERE item_name = %s"
                  query2 = "SELECT price FROM food_items WHERE item_name = %s"

                  cursor.execute(query1,(key,)) #get the item_id of ordered food
                  item_ID = cursor.fetchone()[0]
                  # dispatcher.utter_message(str(item_ID))
                  cursor.execute(query2,(key,))   #get the price of ordered_food
                  price=cursor.fetchone()[0]
                  # dispatcher.utter_message(str(price))

                  
                  insert_query = "INSERT INTO ordered_items (order_id, item_id, quantity,price) VALUES (%s, %s, %s,%s)"

                  # Data to insert
                  data = (newOrderId, item_ID, quantity,price*quantity)

                  # Execute the INSERT query
                  cursor.execute(insert_query, data)
                  conn.commit()    #to store in ordered_items table


            #calculate the total price 
            query4="SELECT SUM(price) FROM ordered_items where order_id=%s"
            cursor.execute(query4,(newOrderId,))
            sum=cursor.fetchone()[0]
            

            # also store in orders table
            query3="INSERT INTO orders (order_id,date,total_price) VALUES (%s,%s,%s)"
            date= datetime.date.today()
            data1 = (newOrderId, date,sum)
            cursor.execute(query3,data1)

            #store the order in track table
            query5="INSERT INTO track_status (order_id,status) VALUES (%s,%s)"
            data2=(newOrderId,"pending")
            cursor.execute(query5,data2)


            conn.commit()  #store in orders table
            cursor.close()
       

            dispatcher.utter_message("बधाई हो आपका आर्डर पूरा हो गया है \n ")
            dispatcher.utter_message("आपके आर्डर की कुल कीमत :रु"+ str(sum))
            dispatcher.utter_message("ये रही आपकी आर्डर ID :"+str(newOrderId))
            dispatcher.utter_message("आर्डर ट्रैक करने के लिए ट्रैक [आर्डर ID] लिखे ")

            my_dict.clear()  #remove all items from order so that new order can be started
            return []

# track order
class TrackOrder(Action):
      def name(self):
            return "action_track_order"

      def run(self, dispatcher, tracker, domain):
            entities = tracker.latest_message['entities']
            cursor = conn.cursor()
            if len(entities)==0:
                  dispatcher.utter_message("आर्डर ट्रैक करने के लिए ट्रैक [आर्डर ID] लिखे")
            else:
                  id=int(entities[0]["value"])
                  query6="SELECT status FROM track_status where order_id=%s"
                  cursor.execute(query6,(id,))
                  status=cursor.fetchone()
                  if status:
                        dispatcher.utter_message(str(status[0]))
                  else:
                        dispatcher.utter_message("कोई टैक स्टेटस नहीं मिला .")
                  

            cursor.close()
            return []
      

# to clear conversation
class ClearConversation(Action):
      def name(self):
            return "action_clear_conversation"

      def run(self, dispatcher, tracker, domain):
            
            return [AllSlotsReset(), Restarted()]

class ActionRestart(Action):

  def name(self):
      return "action_restart"

  def run(
      self, dispatcher, tracker: Tracker, domain: Dict[Text, Any]
  ) -> List[Dict[Text, Any]]:

      # tracker.clear()
      dispatcher.utter_message("haveli")
      return [SlotSet(slot, None) for slot in tracker.slots]
      #dispatcher.utter_message("Conversation history cleared.")
      # custom behavior

      return [...]