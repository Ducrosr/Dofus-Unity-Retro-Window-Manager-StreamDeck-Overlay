# Plugin Stream Deck — Dofus Window Manager

Le plugin communique uniquement avec Dofus Window Manager sur `127.0.0.1:32145`. Il ne lit pas la mémoire du jeu et n'envoie aucune action en jeu : il active seulement une fenêtre Windows.

> [!WARNING]
> Installe uniquement le paquet fourni par le [dépôt officiel](https://github.com/Ducrosr/Dofus-Unity-Retro-Window-Manager-StreamDeck-Overlay). Le plugin officiel ne demande jamais d’identifiant Ankama, de mot de passe, de code d’authentification ou de jeton de session.

La version 0.7.0 ordonne les fenêtres qui demandent l’attention (`!1`, `!2`…) et ajoute l’action **Prochaine alerte**, qui affiche le nombre restant et active la demande la plus ancienne. Le léger clignotement reste facultatif et synchronisé avec l’application. Le plugin peut afficher le portrait ainsi qu’une des 39 icônes officielles de caractéristiques ou 20 icônes officielles de métiers intégrées, et reprend automatiquement le thème ainsi que la langue transmis par l’application. Les douze thèmes de l’application sont compatibles avec Unity comme avec Retro. Il conserve le secours Windows des actions Personnage, Suivant, Précédent et Prochaine alerte : si Stream Deck garde le premier plan, le plugin réduit sa propre fenêtre puis répète la commande une fois. Le script PowerShell fourni vérifie strictement que la fenêtre active appartient bien à Stream Deck avant toute réduction.

## Développement et installation locale

Prérequis : Node.js 24 ou ultérieur, Stream Deck 7.1 ou ultérieur et `@elgato/cli`.

Dans PowerShell, depuis ce dossier :

```powershell
npm ci
npm run build
streamdeck link com.remyducros.dofuswindowmanager.sdPlugin
```

Lors de la première installation, Stream Deck propose automatiquement le profil modifiable **Dofus Window Manager** pour les modèles standard à 15 touches. Il contient huit touches Personnage et toutes les commandes, disposées comme suit : **Monter** puis personnages 1 à 4 sur la première ligne, **Descendre** puis personnages 5 à 8 sur la deuxième, et **Lancer / afficher**, **Ignorer**, **Actualiser**, **Précédent**, **Suivant** sur la dernière ligne.

Lance le gestionnaire manuellement une première fois : il enregistre automatiquement sa commande de démarrage dans `%APPDATA%\DofusUnityWindowManager\streamdeck-launcher.json`. La touche **Lancer / afficher** utilise ensuite cet emplacement, que l’application soit exécutée depuis les sources Python ou sous forme d’exécutable. Si le gestionnaire est déjà ouvert, la même touche ramène simplement sa fenêtre au premier plan.

Lance ensuite Dofus Window Manager, ouvre les clients Dofus et effectue un scan. Les touches Personnage utilisent par défaut le numéro ligne 1, le nom ligne 2, la classe ligne 3 et l’alias ligne 4. Ces éléments peuvent ensuite être masqués ou déplacés indépendamment. Une couleur de bordure peut représenter Terre, Feu, Eau, Air, Neutre ou Violet. Les touches suivent l’ordre de l’application, tandis que la mise en page et la couleur restent stockées par personnage et le suivent lorsqu’il change de touche. Sans alias, la ligne affiche `—`. Un alias court comme l’élément joué (`Terre`, `Feu`, `Eau`, `Air`) ou un métier (`Mineur`, `Alchimiste`…) facilite la lecture en cas de pseudos proches ou de classes en doublon.

Lors de la première utilisation d’une version prenant en charge les préférences par personnage, les choix déjà présents sur les touches sont automatiquement associés aux personnages correspondants.

La liste sépare le nom et la classe même lorsque leur ordre varie dans le titre de la fenêtre Dofus. Si un ancien scan ou un alias contient la classe à la place du nom, le plugin retrouve le nom depuis le titre de la fenêtre.

Pour recompiler automatiquement pendant le développement :

```powershell
npm run watch
```

Contrôles avant diffusion :

```powershell
npm run typecheck
npm run validate
npm run pack
```

Le bouton affiche `DWM fermé` si le gestionnaire n'est pas lancé, ou `Personnage indisponible` si sa fenêtre n'existe plus. La fenêtre actuellement active utilise l'état visuel vert.

Les actions **Monter le personnage** et **Descendre le personnage** ciblent en priorité la fenêtre Dofus au premier plan, puis le personnage actif du gestionnaire. Elles déplacent le personnage d’une position sans boucler aux extrémités et synchronisent immédiatement les touches. Une fenêtre ignorée doit être réintégrée avant d’être déplacée.

L’action **Actualiser** attend la fin du scan demandé avant d’afficher sa confirmation. **Ignorer / réintégrer** utilise la même règle de ciblage. Une fenêtre ignorée reste dans la liste, conserve son bouton et peut toujours être activée directement ; seules les actions **Suivant** et **Précédent** l’évitent. Les autres personnages changent de touche lorsque leur ordre est modifié dans l’application ou depuis le Stream Deck.

L’action **Prochaine alerte** peut être ajoutée librement à n’importe quelle touche du profil. Elle reste neutre lorsque la file est vide, puis affiche `!` et le nombre de demandes en orange. Une pression active `!1` sans modifier l’ordre de rotation.
