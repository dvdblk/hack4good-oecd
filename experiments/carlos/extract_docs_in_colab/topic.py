from typing import Optional
import pandas as pd
import re

class Topic:
    def __init__(self,
                 name: list[str] | str,
                 subtopics: Optional[list['Topic']] = None
                 ) -> None:
        """ name can have several names for stability. Most relevant name first.
        """

        if type(name) == str:
            self.name = [name]
        else:
            self.name = name

        self.subtopics = subtopics
        self.replies = {}
        return

    def add_reply(self, question_id, answer):
        self.replies[question_id] = answer
        return


def recursive_topic_creator(df: pd.DataFrame, parent: Optional[str] = None):
    """ recursively find subtopics and create an internal dependency tree
    not currently working
    """

    if parent is None:
        top_level_topics = df[df['parent'].isna()]
    else:
        top_level_topics = df[df['parent'] == parent]

    if top_level_topics.empty:
        return [Topic(parent)]

    topics = []
    for idx in range(len(top_level_topics)):

        names = [top_level_topics.iloc[idx]['name']]

        if not pd.isna(top_level_topics.iloc[idx]['othernames']):
            names += re.split(r',\s*', top_level_topics.iloc[idx]['othernames'])

        subtopics = []
        if not pd.isna(top_level_topics.iloc[idx]['subtopics']):
            # print("working on ", names)
            subtopic_names = re.split(r',\s*', top_level_topics.iloc[idx]['subtopics'])
            for st in subtopic_names:
                subtopics += recursive_topic_creator(df, st)

        topics.append(Topic(names, subtopics))

    return topics