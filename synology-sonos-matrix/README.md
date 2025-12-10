# Sonos Network Matrix pour Synology

Ce dossier ajoute un petit serveur web (Flask) qui scanne les enceintes SONOS (port 1400) sur une plage IP et affiche une matrice réseau colorée à la manière de l'outil S2. L'application écoute par défaut sur le port `9200` et propose un bouton de rafraîchissement de l'état.

## Fonctionnalités
- Découverte des appareils SONOS sur une plage IP configurée.
- Lecture et parsing du statut `/status/perf` de chaque appareil.
- Affichage HTML avec code couleur (bon / moyen / mauvais) et formulaire de rafraîchissement.
- Port par défaut : `9200` (modifiable via variable d'environnement `PORT`).

## Exécution rapide (tests locaux ou conteneur Synology)
```bash
cd synology-sonos-matrix
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m sonos_matrix.app --host 0.0.0.0 --port 9200 --subnet 192.168.1. --range 1-254
```
Ensuite ouvrez `http://<NAS>:9200/`.

Variables d'environnement utiles :
- `PORT` : port du serveur web (défaut 9200)
- `SONOS_SUBNET` : préfixe du réseau (ex: `192.168.1.`)
- `SONOS_RANGE` : plage IP ex: `1-254`
- `SONOS_TIMEOUT` : timeout TCP pour la découverte (secondes)

## Squelette de paquet Synology (SPK)
Le dossier `spk/` contient un squelette minimal pour produire un paquet DSM :
- `INFO` : métadonnées du paquet.
- `scripts/start-stop-status` : script init (crée un venv, installe les dépendances, lance le serveur sur 0.0.0.0:9200 par défaut).

### Construction d'un SPK
1. Préparer l'arborescence du paquet dans `build/` (contenu de `sonos_matrix`, `requirements.txt`, etc.). Un exemple :
   ```bash
   cd synology-sonos-matrix
   mkdir -p build/sonos-matrix/var
   cp -r sonos_matrix requirements.txt build/sonos-matrix/
   cp -r spk/* build/sonos-matrix/
   ```
2. Ajuster `spk/INFO` si besoin (nom, version, port).
3. Créer l'archive SPK :
   ```bash
   cd build/sonos-matrix
   tar -cvf ../sonos-matrix.spk .
   ```
4. Installer le paquet via le Centre de paquets DSM (menu **Installation manuelle**).

Le script `start-stop-status` supporte les commandes `start`, `stop` et `status` utilisées par DSM. Le serveur est démarré en arrière-plan et écrit le log dans `${SYNOPKG_PKGVAR}/server.log`.

## Ports
L'application écoute sur le port `9200` pour correspondre à la demande. Vérifiez que le port est libre sur votre NAS et exposez-le si vous utilisez Docker.
