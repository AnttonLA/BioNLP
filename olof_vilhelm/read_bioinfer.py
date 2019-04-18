import sys
import xml.etree.cElementTree as ET


class BioInfer:
    NEGATIVE_CLASSES = {"INHIBIT", "DOWNREGULATE", "SUPPRESS"}
    POSITIVE_CLASSES = {"MEDIATE", "UPREGULATE", "STIMULATE", "ACTIVATE", "CATALYZE"}

    def __init__(self, filename):
        self.__sentences = list()
        self.__tokens = dict()
        self.__subtokens = dict()
        self.__dependencies = dict()
        self.__entities = dict()
        self.__relationships = dict()

        self.__t_id_t_index_dict = dict()
        self.__st_id_st_index_dict = dict()
        self.__e_id_e_index_dict = dict()

        root = ET.parse(filename).getroot()
        if root.tag == "bioinfer":
            sentences = root.find("sentences")
            for sntnc in sentences.findall("sentence"):
                s_id = sntnc.attrib["id"]
                s_text = sntnc.attrib["origText"]
                s = {"text": s_text, "id": s_id}
                self.__sentences.append(s)

                self.__tokens[s_id] = list()
                self.__subtokens[s_id] = list()
                self.__t_id_t_index_dict[s_id] = dict()
                self.__st_id_st_index_dict[s_id] = dict()
                t_counter = 0
                st_counter = 0
                for tkn in sntnc.findall("token"):
                    t_id = tkn.attrib["id"]
                    t_text = ""

                    for subtoken in tkn.findall("subtoken"):
                        t_text += subtoken.attrib["text"]
                        st_id = subtoken.attrib["id"]
                        st_text = subtoken.attrib["text"]
                        sbtkn = {"text": st_text, "id": st_id}
                        self.__subtokens[s_id].append(sbtkn)
                        self.__st_id_st_index_dict[s_id][st_id] = st_counter
                        st_counter += 1

                    t = {"text": t_text, "id": t_id}
                    self.__tokens[s_id].append(t)
                    self.__t_id_t_index_dict[s_id][t_id] = t_counter
                    t_counter += 1

                self.__dependencies[s_id] = list()
                links = None
                for lnkg in sntnc.find("linkages").findall("linkage"):
                    if lnkg.attrib["type"] == "stanford":
                        links = lnkg
                        break

                for link in links.findall("link"):
                    t_id_1 = link.attrib["token1"]
                    t_id_2 = link.attrib["token2"]
                    deprel = link.attrib["type"]
                    if deprel == "None":
                        continue
                    head_id = None
                    word_id = None
                    if "<" in deprel:
                        head_id = t_id_2
                        word_id = t_id_1
                    elif ">" in deprel:
                        head_id = t_id_1
                        word_id = t_id_2

                    deprel = deprel.replace("<", "").replace(">", "")
                    head_index = self.__t_id_t_index_dict[s_id][head_id]
                    word_index = self.__t_id_t_index_dict[s_id][word_id]
                    dpndncy = {
                        "deprel": deprel,
                        "head": head_index,
                        "word": word_index,
                        "head_id": head_id,
                        "word_id": word_id
                    }
                    self.__dependencies[s_id].append(dpndncy)

                self.__entities[s_id] = list()
                self.__e_id_e_index_dict[s_id] = dict()
                e_counter = 0
                for entity in sntnc.findall("entity"):
                    e_id = entity.attrib["id"]
                    e_type= entity.attrib["type"]
                    e_st_ids = list()
                    for e_sbtkns in entity.findall("nestedsubtoken"):
                        e_st_ids.append(e_sbtkns.attrib["id"])
                    e_text = ""
                    for e_st_id in e_st_ids:
                        e_st_index = self.__st_id_st_index_dict[s_id][e_st_id]
                        e_text += self.__subtokens[s_id][e_st_index]["text"]

                    ntty = {
                        "id": e_id,
                        "type": e_type,
                        "text": e_text,
                        "st_ids": e_st_ids
                    }
                    self.__entities[s_id].append(ntty)
                    self.__e_id_e_index_dict[s_id][e_id] = e_counter
                    e_counter += 1

                self.__relationships[s_id] = list()
                for formula in sntnc.find("formulas").findall("formula"):
                    rel_e = formula.find("relnode")
                    if "entity" in rel_e.attrib:
                        rel_e_id = rel_e.attrib["entity"]
                    rel_bioinfer_class = rel_e.attrib["predicate"]

                    rel_entities = rel_e.findall("entitynode")
                    if len(rel_entities) == 2:
                        source_entity_id = rel_entities[0].attrib["entity"]
                        target_entity_id = rel_entities[1].attrib["entity"]
                        source_entity_index = self.__e_id_e_index_dict[s_id][source_entity_id]
                        target_entity_index = self.__e_id_e_index_dict[s_id][target_entity_id]
                        rel_class = "OTHER"
                        if rel_bioinfer_class in BioInfer.NEGATIVE_CLASSES:
                            rel_class = "NEGATIVE"
                        elif rel_bioinfer_class in BioInfer.POSITIVE_CLASSES:
                            rel_class = "POSITIVE"

                        rel_fine_class = ""
                        if "entity" in rel_e.attrib:
                            rel_e_index = self.__e_id_e_index_dict[s_id][rel_e_id]
                            rel_fine_class = self.__entities[s_id][rel_e_index]["text"]
                        rltnshp = {
                            "source": source_entity_index,
                            "target": target_entity_index,
                            "class": rel_class,
                            "fine_class": rel_fine_class,
                            "bioinfer_class": rel_bioinfer_class,
                            "bioinfer_rel_entity_index": rel_e_index
                        }
                        self.__relationships[s_id].append(rltnshp)

        else:
            print("File \'" + filename + "\' is not a bioinfer corpus.")
            exit(1)

    def sentences(self):
        return self.__sentences

    def tokens(self, sentence_id):
        return self.__tokens[sentence_id]

    def dependencies(self, sentence_id):
        return self.__dependencies[sentence_id]

    def entities(self, sentence_id):
        return self.__entities[sentence_id]

    def relationships(self, sentence_id):
        return self.__relationships[sentence_id]


# SEE HERE FOR USAGE OF BioInfer CLASS
if __name__ == "__main__":

    # JUST SOME COMMAND-LINE OPTIONS
    SENTENCE_NR = 0
    if len(sys.argv) > 1:
        try:
            SENTENCE_NR = int(sys.argv[1])
            print("Analyzing sentence " + str(SENTENCE_NR) + ".")
        except ValueError:
            print("Second argument isn't a number. Analyzing (default) sentence 0.")
    else:
        print("Analyzing (default) sentence 0. Pass a number as the second argument to analyze that sentence instead.")


    # MAIN USE OF BioInfer CLASS
    fn = "corpus/BioInfer_corpus_1.1.1.xml"
    print("Reading file: '" + fn + "'.")
    bioinfer = BioInfer(fn)
    sentence = bioinfer.sentences()[SENTENCE_NR]
    tokens = bioinfer.tokens(sentence["id"])
    dependencies = bioinfer.dependencies(sentence["id"])
    entities = bioinfer.entities(sentence["id"])
    relationships = bioinfer.relationships(sentence["id"])

    print("\nSentence " + str(SENTENCE_NR) + ", id:", sentence["id"])
    print(sentence["text"])

    print("\nEntities:")
    for entity in entities:
        print(entity["text"] + "\t" + entity["type"] + "\t(" + entity["id"] + ")")

    print("\nRelationships:")
    if len(relationships) == 0:
        print("No relationships.")
    for relation in relationships:
        src_index = relation["source"]
        src_text = tokens[src_index]["text"]
        tgt_index = relation["target"]
        tgt_text = tokens[tgt_index]["text"]

        rel_class = relation["class"]
        fine_rel_class = relation["fine_class"]
        print(src_text + " [" + str(src_index) + "]\t" + rel_class + "(" + fine_rel_class + ")" + "\t" + tgt_text + " [" + str(tgt_index) + "]")

    print("\nTokens:")
    for i in range(len(tokens)):
        token = tokens[i]
        print(str(i) + "\t" + token["text"] + "\t(" + token["id"] + ")")



    print("\nDependencies:")
    for dependency in dependencies:
        h_index = dependency["head"]
        w_index = dependency["word"]
        h_text = tokens[h_index]["text"]
        w_text = tokens[w_index]["text"]
        print(dependency["deprel"] + "\t" + h_text + " [" + str(h_index) + "]\t" + w_text + " [" + str(w_index) + "]")
