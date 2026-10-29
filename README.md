# ChopzTsushima

Resource-Pack im Stil von **Ghost of Tsushima** für Minecraft 1.20.1 und das
[TruTopia-Modpack](https://modrinth.com/project/yzxnGSON) (Forge, Create, Distant Horizons).
Gedacht als Gegenstück zum Shader [ChopzCinema](https://github.com/ChopstickGuy/ChopzCinema).

- 16x, Blöcke bleiben erkennbar – neu sind Farben, Stimmung und weniger Texturrauschen
- Biom-Farben: Ebenen/Savanne goldenes Susuki-Gras, Wälder roter Ahorn, Birkenwald Ginkgo,
  Wiesen/Kirschhain frisches Grün, Taiga dunkle Zedern
- Hohes Gras mit Pampas-Rispen, Mohn als rote Spinnenlilie (Higanbana), Glyzinien-Azaleen
- Japanische Baumaterialien: Kawara-Dachziegel (Tiefenschiefer-Fliesen), Putz (weiße
  Keramik/Beton), Schrein-Zinnober (rote Keramik/Beton), Papierlaternen
- Buschiges Laub auf Basis von Better Leaves (MIT, © Motschen) – sieht mit und ohne
  Better Leaves gleich aus

## Installation

Die ZIP aus den [Releases](../../releases) in den `resourcepacks`-Ordner legen und im Spiel
**ganz oben** in der Liste aktivieren (über Better Leaves, Fancy Crops usw.).

## Bauen

Die Texturen werden aus den Vanilla-Texturen generiert (die nicht im Repo liegen):

```bash
uv venv .venv && uv pip install --python .venv/bin/python pillow numpy
scripts/fetch_vanilla.sh            # oder: scripts/fetch_vanilla.sh /pfad/zu/1.20.1.jar
.venv/bin/python scripts/build.py   # -> pack/ChopzTsushima
```

`scripts/sheet.py` erzeugt eine Vorschau-Tafel der Texturen mit Biom-Färbung.
