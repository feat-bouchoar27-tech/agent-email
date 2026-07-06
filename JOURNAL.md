# Journal de bord — Agent IA Famasser

## 02/07/2026

- Correction d'un bug de fiabilité dans `outlook_connector.py` : la fonction 
  `get_emails_non_lus()` utilisait le numéro de séquence IMAP comme identifiant 
  unique d'email, ce qui n'est pas stable dans le temps. Remplacé par le vrai 
  header `Message-ID` (RFC 822), garanti unique et stable.
- Raccourcissement des prompts IA dans `ai_processor.py` suite au retour de 
  M. Mohim (résumés et réponses proposées trop longs) : résumé réduit à 1 phrase 
  (15 mots max), réponse réduite à 2 phrases courtes (10 mots max chacune).
- Tests effectués avec plusieurs emails de test envoyés vers testagentia@famasser.ma 
  pour valider le comportement.