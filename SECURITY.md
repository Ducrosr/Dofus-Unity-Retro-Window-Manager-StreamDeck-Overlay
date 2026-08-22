# Politique de sécurité

## Source officielle

L’unique dépôt officiel de Dofus Window Manager est :

<https://github.com/Ducrosr/Dofus-Retro-64-Window-Manager>

Les sources, futurs binaires et paquets Stream Deck officiels doivent provenir de ce dépôt ou de ses Releases. Un fichier distribué sur un autre site, un hébergeur de fichiers, Discord ou par message privé doit être considéré comme non vérifié, même s’il reprend le même nom, la même icône ou des captures d’écran officielles.

## Ce que la version officielle ne demande jamais

Dofus Window Manager ne demande jamais :

- un identifiant ou un mot de passe Ankama ;
- un code de double authentification ;
- un jeton de session ou un cookie ;
- l’accès à une boîte mail ;
- la désactivation de l’antivirus ;
- l’installation d’un certificat ;
- l’exécution d’une commande téléchargée depuis un tiers.

Si une copie demande l’un de ces éléments, fermez-la, déconnectez le PC du réseau si nécessaire, effectuez une analyse de sécurité et changez les secrets potentiellement exposés depuis un appareil sain.

## Architecture de sécurité

L’application officielle :

- énumère les fenêtres Windows visibles et manipule leur premier plan ;
- ne lit et ne modifie pas la mémoire de Dofus ;
- n’injecte pas de code et n’installe aucun hook dans le processus du jeu ;
- ne capture pas les identifiants, le clavier du jeu ou les paquets réseau ;
- stocke ses réglages, profils et journaux dans %APPDATA%\DofusUnityWindowManager\ ;
- expose au plugin Stream Deck un petit pont HTTP lié exclusivement à 127.0.0.1:32145 ;
- refuse les commandes portant un en-tête Origin de navigateur et limite la taille des requêtes ;
- ne contacte aucun serveur externe depuis le cœur Python.

Le panneau de propriétés Stream Deck utilise les composants officiels Elgato chargés depuis sdpi-components.dev. Le plugin communique avec l’application uniquement par l’adresse locale ci-dessus.

Un petit script PowerShell inclus dans le plugin peut réduire l’application Stream Deck lorsque Windows refuse de donner le premier plan à Dofus. Il vérifie que la fenêtre active appartient bien à Stream Deck avant d’agir.

## Privilèges Windows

Le gestionnaire doit fonctionner au même niveau de privilèges que Dofus. Le mode administrateur n’est ni demandé ni recommandé par défaut. Utilisez-le uniquement si le client Dofus est lui-même lancé en administrateur et après avoir vérifié la provenance du programme.

## Vérifier un téléchargement

1. Contrôlez que l’adresse commence exactement par https://github.com/Ducrosr/Dofus-Retro-64-Window-Manager/.
2. Préférez une Release rattachée à un tag et à des notes de version.
3. Comparez le SHA-256 publié lorsqu’un binaire est proposé.
4. Analysez le fichier avec Microsoft Defender ou un service de réputation reconnu.
5. En cas de doute, exécutez les sources après les avoir examinées ou attendez une version vérifiée.

Un avertissement SmartScreen peut provenir de l’absence de signature numérique, mais il ne constitue pas une preuve de sécurité. La provenance, le code source et l’empreinte restent essentiels.

## Versions prises en charge

| Version | Statut sécurité |
|---|---|
| 2.19.x | prise en charge pendant la bêta actuelle |
| versions antérieures | mise à jour recommandée avant tout rapport |

## Signaler une vulnérabilité

Ne publiez jamais de secret, de preuve contenant des identifiants, ni de procédure immédiatement exploitable dans une Issue publique.

Utilisez en priorité **Security → Report a vulnerability** sur le dépôt si l’option est disponible. À défaut, ouvrez une Issue minimale indiquant qu’un contact privé est nécessaire, sans détail sensible. Pour un bug ordinaire sans impact de sécurité, utilisez le formulaire de rapport de bug.

Indiquez la version, Windows, la version du plugin concernée, le scénario et l’impact. N’incluez pas le dossier de données complet : les journaux peuvent contenir des pseudos et des chemins locaux.
