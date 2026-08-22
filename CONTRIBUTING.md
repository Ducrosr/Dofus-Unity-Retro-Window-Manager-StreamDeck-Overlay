# Participer au projet

Merci de contribuer à la bêta de Dofus Window Manager. Les rapports reproductibles et les retours d’ergonomie sont aussi utiles que les contributions de code.

## Avant d’ouvrir un ticket

1. utilisez la dernière version disponible sur le dépôt officiel ;
2. recherchez un ticket existant ;
3. reproduisez le problème après un scan manuel ;
4. ouvrez **Diagnostic…** et copiez le rapport ;
5. retirez les pseudos, chemins ou autres données que vous ne souhaitez pas rendre publiques.

Ne publiez jamais d’identifiant Ankama, de mot de passe, de code de double authentification, de jeton de session ou d’adresse électronique. Pour une vulnérabilité, suivez [SECURITY.md](SECURITY.md).

## Rapport de bug utile

Précisez :

- la version de Dofus Window Manager ;
- Unity ou Retro ;
- Windows 10 ou 11 et sa version ;
- Stream Deck et la version du plugin si concernés ;
- le nombre de fenêtres ouvertes ;
- le résultat attendu et le résultat obtenu ;
- les étapes exactes de reproduction ;
- le rapport de diagnostic nettoyé ;
- une capture d’écran si elle n’expose aucune donnée sensible.

Pour un problème de détection, fournissez le titre de fenêtre après avoir remplacé le pseudo par un exemple neutre. Pour un problème de focus, indiquez l’application qui se trouvait au premier plan et si un programme était lancé en administrateur.

## Proposer une amélioration

Décrivez le besoin utilisateur avant la solution technique : situation actuelle, difficulté rencontrée, comportement souhaité et éventuels compromis. Les propositions liées à l’injection, à l’automatisation d’actions en jeu, à la lecture mémoire ou à l’interception réseau ne correspondent pas au périmètre du projet.

## Développement local

~~~powershell
git clone https://github.com/Ducrosr/Dofus-Retro-64-Window-Manager.git
cd Dofus-Retro-64-Window-Manager
py -3.14 -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r requirements.txt -r requirements-dev.txt
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
.\.venv\Scripts\python.exe -m ruff check .
~~~

Pour le plugin :

~~~powershell
cd streamdeck-plugin
npm ci
npm test
npm run typecheck
npm run build
~~~

Le guide complet se trouve dans [docs/COMPILATION.md](docs/COMPILATION.md).

## Pull requests

- créez une branche dédiée ;
- limitez la PR à un sujet ;
- ajoutez ou adaptez les tests ;
- mettez à jour la documentation pour toute fonction visible ;
- n’ajoutez pas de fichiers générés, de données personnelles, de profils locaux ou de journaux ;
- expliquez les tests manuels effectués sous Windows.

Le projet privilégie les fonctions locales, explicites et auditables. Toute modification des privilèges, du pont local, du script PowerShell ou de la capture Retro doit inclure une analyse de sécurité dans la PR.
