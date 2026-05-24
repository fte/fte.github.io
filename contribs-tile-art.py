#!/usr/bin/env python3
# draw_contrib.py (version avec simulation)

import sys
import subprocess
import argparse
from datetime import datetime, timedelta, timezone

def run(cmd, check=True):
    res = subprocess.run(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if check and res.returncode != 0:
        print(f"Command failed: {cmd}\nstdout:\n{res.stdout}\nstderr:\n{res.stderr}")
        sys.exit(1)
    return res

def git_init_check():
    res = subprocess.run("git rev-parse --is-inside-work-tree", shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if res.returncode != 0:
        print("Ce dossier n'est pas un repo git. Initialisez-en un (git init) ou clonez-en un existant.")
        sys.exit(1)

def parse_art(path):
    lines = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            lines.append(line.rstrip("\n"))
    while lines and lines[-1] == "":
        lines.pop()
    if len(lines) != 7:
        print(f"Le fichier doit contenir exactement 7 lignes (une par jour: dim->sam). Trouvé: {len(lines)}")
        sys.exit(1)
    widths = set(len(l) for l in lines)
    print(widths)
    if len(widths) != 1:
        print("Toutes les lignes doivent avoir la même largeur.")
        sys.exit(1)
    width = widths.pop()
    if width > 52:
        print("Largeur max 52 colonnes.")
        sys.exit(1)
    return lines, width

def build_dates(width, align_right=True):
    today = datetime.now(timezone.utc).date()
    weekday = today.weekday()  # Monday=0..Sunday=6
    days_to_sub = (weekday + 1) % 7
    this_sunday = today - timedelta(days=days_to_sub)
    week_starts = []
    for i in range(width):
        delta_weeks = width - 1 - i if align_right else i
        wk_start = this_sunday - timedelta(weeks=delta_weeks)
        week_starts.append(wk_start)
    return week_starts

def make_commit_for_date(commit_message, file_path, commit_date, commits_per_cell=1):
    dt = datetime(commit_date.year, commit_date.month, commit_date.day, 12, 0, 0, tzinfo=timezone.utc)
    date_iso = dt.isoformat()
    for c in range(commits_per_cell):
        with open(file_path, "a", encoding="utf-8") as f:
            f.write(f"{date_iso} - commit {c}\n")
        subprocess.run(f"git add {file_path}", shell=True)
        env_cmd = f'GIT_AUTHOR_DATE="{date_iso}" GIT_COMMITTER_DATE="{date_iso}" git commit -m "{commit_message} ({date_iso})" --no-gpg-sign'
        subprocess.run(env_cmd, shell=True)

# --- Nouvelle fonction simulation ---
def simulate_contribs(lines, commits_per_cell=1):
    colors = [
        "\033[48;5;255m  \033[0m",  # 0 commit -> blanc
        "\033[48;5;120m  \033[0m",  # 1-2 -> très clair vert
        "\033[48;5;34m  \033[0m",   # 3-4 -> moyen vert
        "\033[48;5;28m  \033[0m",   # 5-7 -> foncé
        "\033[48;5;22m  \033[0m"    # 8+ -> très foncé
    ]
    print("Simulation de la grille GitHub :\n")
    for row in lines:
        row_str = ""
        for ch in row:
            if ch in ("#", "X", "1"):
                commits = commits_per_cell
                if commits >= 8: color = colors[4]
                elif commits >= 5: color = colors[3]
                elif commits >= 3: color = colors[2]
                elif commits >= 1: color = colors[1]
            else:
                color = colors[0]
            row_str += color
        print(row_str)
    print("\nLégende : plus foncé = plus de commits.\n")

def main():
    parser = argparse.ArgumentParser(description="Dessine sur le tableau de contributions GitHub ou simule la grille.")
    parser.add_argument("artfile", help="Fichier ASCII (7 lignes).")
    parser.add_argument("--left", action="store_true", help="Aligner à gauche au lieu de droite.")
    parser.add_argument("--commits-per-cell", type=int, default=1, help="Nombre de commits par case active.")
    parser.add_argument("--target-file", default="contrib_art.txt", help="Fichier modifié pour commits.")
    parser.add_argument("--message", default="contrib art", help="Message de commit de base.")
    parser.add_argument("--simulate", action="store_true", help="Simule la grille GitHub dans le terminal au lieu de créer les commits.")
    args = parser.parse_args()

    lines, width = parse_art(args.artfile)
    align_right = not args.left

    if args.simulate:
        simulate_contribs(lines, commits_per_cell=args.commits_per_cell)
        return

    git_init_check()
    week_starts = build_dates(width, align_right=align_right)
    print(f"Art {width} cols x 7 rows. Création des commits...")

    for col in range(width):
        for row in range(7):
            ch = lines[row][col]
            if ch in ("#", "X", "1"):
                target_date = week_starts[col] + timedelta(days=row)
                print(f"→ Commit pour {target_date.isoformat()} (col {col}, row {row})")
                make_commit_for_date(args.message, args.target_file, target_date, commits_per_cell=args.commits_per_cell)

    print("Terminé. Push vers GitHub pour voir le tableau.")

if __name__ == "__main__":
    main()
