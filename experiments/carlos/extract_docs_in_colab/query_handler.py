import time
import copy
from pydantic.networks import KafkaDsn
from topic import Topic
import openai
import json
import tenacity

class QueryHandler:
    def __init__(self, 
                 topics: list['Topic'], 
                 question_dict, 
                 vectorstore,
                 rag_topk: int = 8,
                 model_name: str = "gpt-3.5-turbo-1106",
                 query_json_split_size: int = 2,
                 sleep_time: int = 0.2):

        self.topics = topics
        self.original_topics = copy.deepcopy(self.topics)

        self.question_dict = question_dict

        self.vectorstore = vectorstore
        self.rag_topk = rag_topk
        self.model_name = model_name
        self.query_json_split_size = query_json_split_size
        self.sleep_time = sleep_time

        return

    @tenacity.retry(
        wait=tenacity.wait_fixed(1) + tenacity.wait_random(0, 1),
        stop=tenacity.stop_after_attempt(10))
    def run_query(self, rag_call, llm_call, dict_keys=None):
        rag_resp = self.vectorstore.similarity_search(rag_call, k=self.rag_topk)
        query_wrapper = """Answer the questions at the end based only on the following excerpts of a policy document:
        If something is not mentioned reply 0, do not make up things.
        {context}
        Question: {question}
        """
        context = ""

        rag_resp.reverse() # reverse rag doc order
        for sim in rag_resp:
            context += sim.page_content + "\n"

        query = query_wrapper.format(context=context, question=llm_call)

        client = openai.OpenAI()

        response = client.chat.completions.create(
            model=self.model_name,
            messages=[
                {"role": "system", "content": "You are a helpful assistant helping to classify policy documents."},
                {"role": "user", "content": query}
            ],
            response_format={ "type": "json_object" },
            timeout = 7
        )
        resp_dict = json.loads(response.choices[0].message.content)

        # print("debug: ")
        # print("resp_dict: ", resp_dict.keys(), ", dict_keys: ", dict_keys)

        # if not dict_keys is None:
        #     print(dict_keys)

        if not dict_keys is None and dict_keys != resp_dict.keys():
            print("KEYS DONT MATCH")
            print("is: ", resp_dict)
            print("should: ", dict_keys)
            raise ValueError("Keys dont match!")

        return resp_dict


    def traverse_basic(self):

        self.results_binary = {}

        for topic in self.topics:
            print(f"Working on {topic.name[0]}...")

            top_dict = self.question_dict["top"]
            rel_dict = self.question_dict["relation"]
            questions = self.question_dict["questions"]

            split_lst = [
                topic.subtopics[
                    x:x+self.query_json_split_size] for x in range(0, len(topic.subtopics), self.query_json_split_size)]
            topic_res = {}
            for sub_chunk in split_lst:
                my_q_dict = {}

                for q in questions: # general questions
                    my_q_dict["general_"+q.title()] = top_dict[q].format(topic=topic.name[0])
                    my_q_dict["general_"+q.title()] += self.question_dict["formatting"][q]

                for sub in sub_chunk: # subtopic questions
                    for q in questions:
                        my_q_dict[sub.name[0]+"_"+q.title()] = rel_dict[q].format(topic=topic.name[0], subtopic=sub.name[0])
                        my_q_dict[sub.name[0]+"_"+q.title()] += self.question_dict["formatting"][q]

                question = "Fill in the following json:\n" + str(my_q_dict)
                question += " Make sure that your response consists of a valid json with all keys identical to the input."

                rag_call = topic.name[0]
                for s in sub_chunk:
                    rag_call += ", " + s.name[0]

                reply = self.run_query(rag_call, question, my_q_dict.keys())
                topic_res.update(reply)
                time.sleep(self.sleep_time)

            
            for k in topic_res.keys():
                if not "binary" in k.lower():
                    continue
                topic_res[k] = int(topic_res[k])
            print(topic_res)
            
            self.results_binary[topic.name[0]] = topic_res


    def traverse_advanced(self, results_binary, questions):
        expanded_dict = {}
        for key in results_binary.keys():
            print(f"Working on {key}...")

            topic_dict = results_binary[key].copy()

            binary_keys = [k for k in topic_dict.keys() if "binary" in k.lower()]

            for bk in binary_keys:

                # compile rag call and topic_name
                parts = bk.split("_")
                if "general" in bk:
                    rag_call = key
                    topic_name = key
                elif len(parts) > 1:
                    rag_call = key + ", " + parts[0]
                    topic_name = parts[0]
                else:
                    rag_call = key + ", " + bk
                    topic_name = bk


                if topic_dict[bk] == 0:
                    for k in questions.keys():
                        for q in questions[k].keys():
                            if "summary" in k:
                                topic_dict[topic_name+"_"+k+"_"+q] = "Not mentioned in document."
                            else:
                                topic_dict[topic_name+"_"+k+"_"+q] = 0
                    continue
                
                
                for k in questions.keys():
                    q_dict = {}
                    for q in questions[k].keys():
                        q_dict[topic_name+"_"+k+"_"+q] = questions[k][q].format(topic=topic_name)
                    
                    question = "Fill in the following json: \n" + str(q_dict)
                    question += "\n Make sure that your response consists only of a valid json with keys identical to the input."
                    
                    reply = self.run_query(rag_call+", "+k, question, dict_keys=q_dict.keys())
                    for k in reply.keys():
                        if not "summary" in k.lower():
                            reply[k] = int(reply[k])

                    topic_dict.update(reply)
            
            # print("finished topic dict: ", topic_dict)
            expanded_dict[key] = topic_dict
        
        return expanded_dict

    

    def run(self):
        self.traverse_basic()
        res = {"content": self.results_binary}
        res["metadata"] = {
            "model": self.model_name,
            "rag_topk": self.rag_topk,
            "questions": self.question_dict
        }
        return res


class DocHandler:
    def __init__(self, 
                 doc_list: list[str]):
        self.doc_list = doc_list
        return
    