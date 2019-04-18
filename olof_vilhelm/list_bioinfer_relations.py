from read_bioinfer import BioInfer

fn = "corpus/BioInfer_corpus_1.1.1.xml"
bioinfer = BioInfer(fn)
for sentence in bioinfer.sentences():
    interesting_sentence = False
    s_id = sentence["id"]
    for relation in bioinfer.relationships(s_id):
        if relation["class"] != "OTHER":
            interesting_sentence = True
            break

    if interesting_sentence:
        print("\nSentence id:", s_id)
        print("  " + sentence["text"])

        print("\nEntities:")
        for entity in bioinfer.entities(s_id):
            print("  " + entity["text"] + "\t" + entity["type"] + "\t(" + entity["id"] + ")")

        relationships = bioinfer.relationships(s_id)
        tokens = bioinfer.tokens(s_id)
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
            print("  " + src_text + " [" + str(
                src_index) + "]\t" + rel_class + "(" + fine_rel_class + ")" + "\t" + tgt_text + " [" + str(
                tgt_index) + "]")

        print("\n######################################################")
