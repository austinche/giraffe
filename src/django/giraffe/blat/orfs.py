
import models
from Bio.Seq import Seq
import math
import tags

trans_table = 1 # standard translation table
min_protein_len = 200

def detect_orfs(sequence_object):
    sequence_object.clear_orf_features()

    # double up sequence, so we can detect features across 0 bp
    # boundary
    seq = Seq(sequence_object.sequence*2)
    seq_len = len(sequence_object.sequence)
    aa_len = math.floor(seq_len/3.0)

    for strand,nuc in [(+1,seq), (-1,seq.reverse_complement())]:
        for frame in range(3):
            #print 'strand '+str(strand)+' frame '+str(frame)

            trans = str(nuc[frame:].translate(trans_table))
            trans_len = len(trans)
            aa_start = 0
            aa_end = 0
            # go through the translation one by one, so we know where
            # the ORFs start and end
            while aa_start < trans_len and aa_start < aa_len:
                #print 'start '+str(aa_start)
                aa_end = trans.find("*", aa_start)
                has_stop = 1
                if aa_end == -1:
                    aa_end = trans_len
                    has_stop = 0

                start_codon = trans.find('M', aa_start, aa_end)

                # is there a start codon?
                if start_codon == -1:
                    assert(aa_end != -1)
                    aa_start = aa_end+1
                    continue

                if aa_end-start_codon >= min_protein_len:
                    #print 'found '+trans[start_codon:aa_end]

                    # the following start and end need to start with
                    # 1, not 0.
                    if strand == 1:
                        start = frame+start_codon*3+1
                        end = frame+aa_end*3+has_stop*3
                        if end > seq_len:
                            end = end % seq_len
                    else:
                        start = seq_len-frame-aa_end*3-has_stop*3+1
                        end = seq_len-frame-start_codon*3
                        if start < 0:
                            start = seq_len+start

                    f = models.Sequence_Feature_Annotated()
                    f.sequence = sequence_object
                    f.feature_name = 'ORF frame '+str(frame+1)
                    f.feature_type_id = models.Feature_Type.ORF
                    f.orf_frame = frame
                    f.start = start
                    f.end = end
                    if strand == 1:
                        f.clockwise = True
                    else:
                        f.clockwise = False
                    f.save()
                    orf_annotated = f
                    print str(f.to_dict())

                    # also try to see if we can find any protein tags
                    # in this ORF
                    for tag in tags.PROTEIN_TAGS:
                        peptide = tags.PROTEIN_TAGS[tag]
                        tag_aa_start = trans.find(peptide,start_codon,aa_end)
                        if tag_aa_start >= 0:
                            tag_aa_end = tag_aa_start+len(peptide)
                            if strand == 1:
                                tag_start = frame+tag_aa_start*3+1
                                tag_end = frame+tag_aa_end*3
                                if tag_end > seq_len:
                                    tag_end = tag_end % seq_len
                            else:
                                tag_start = seq_len-frame-tag_aa_end*3+1
                                tag_end = seq_len-frame-tag_aa_start*3
                                if tag_start < 0:
                                    tag_start = seq_len+tag_start

                            f = models.Sequence_Feature_Annotated()
                            f.sequence = sequence_object
                            f.orf_annotated = orf_annotated
                            f.feature_name = tag
                            f.feature_type_id = models.Feature_Type.FEATURE
                            f.start = tag_start
                            f.end = tag_end
                            if strand == 1:
                                f.clockwise = True
                            else:
                                f.clockwise = False
                            f.save()
                            print str(f.to_dict())

                aa_start = aa_end+1

