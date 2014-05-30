# lower case everything
s/\(.*\)/\L\1/

# common typos
s/colorecal/colorectal/

# simplifications
s/whole//
s/peripheral//
s/primary//

# mappings
s/.*bone marrow.*/bone marrow/

s/.*adipose.*/adipose/

s/.*skeletal muscle.*/skeletal muscle/

s/.*mammary.*/breast/
s/.*breast.*/breast/

s/.*colorectal.*/colon/

s/.*renal.*/kidney/
s/.*kidney.*/kidney/

s/.*gingival.*/gingiva/

s/wbc/leukocyte/
s/.*white blood cell.*/leukocyte/
s/.*leukocyte.*/leukocyte/
s/.*red blood cell.*/erythrocyte/
s/.*blood.*/blood/
s/.*pbmc.*/blood/

s/.*liver.*/liver/
s/.*hepatic.*/liver/
s/.*hepatocyte.*/liver/

s/.*lung.*/lung/
s/.*pneumatic.*/lung/

s/.*cardiac.*/heart/
s/.*heart.*/heart/
s/.*myocard.*/heart/

s/.*brain.*/brain/

s/.*neuron.*/neuron/

s/.*spleen.*/spleen/
s/.*splenocyte.*/spleen/

s/.*thymus.*/thymus/

s/.*ovarian.*/ovary/

s/.*skin.*/skin/
s/.*epidermis.*/skin/

s/.*lymph nodes.*/lymph node/

s/.*prostate.*/prostate/

s/.*pancrea.*/pancreas/

s/.*conjuntiva.*/conjunctiva/

s/.*retina.*/retina/

# remove cancer-related terms (covered in cancer attribute column)
s/tumor//

# trim whitespace
s/^[ \t]*//
s/[ \t]*$//
