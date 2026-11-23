# Données ChainGuard (M1)
Source : X-SPIDE (Pennella et al., IEEE Access 2025), fichier `dataset/DS_deployed_bytecode.csv`
(7 446 contrats, 880 Ponzi). Les données brutes sont dans data/raw/xspide (non commité).

contracts_features.csv
- address : adresse du contrat (minuscules)
- label : 1 = Ponzi, 0 = non-Ponzi (colonne `target` d'origine)
- acc_* : 23 features de compte/transactions d'origine (colonnes 2 à 24 du CSV X-SPIDE)
- op_* : fréquence relative de chaque opcode (76 opcodes ; compte d'origine / n_instr)
- n_instr : nombre total d'instructions (somme des comptes d'opcodes d'origine)
test_ponzi_addresses.csv : Ponzi du jeu de test (split 80/20 stratifié, random_state=42).
