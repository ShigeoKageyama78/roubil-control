// Simulateur de tarif.
// Récupère tous les tarifs via l'API (/api/tarifs, JSON), remplit les listes déroulantes à partir
// de ces données, puis affiche le montant « favorable » et « défavorable » dans le navigateur.
// Le texte est inséré avec textContent (jamais innerHTML) : aucune injection de code possible,
// même si une donnée contenait du HTML.
(function () {
  "use strict";
  const selects = {
    prestation: document.getElementById("sim-prestation"),
    categorie: document.getElementById("sim-categorie"),
    tranche_cv: document.getElementById("sim-cv"),
  };
  const resultat = document.getElementById("sim-resultat");
  if (!selects.prestation || !selects.categorie || !selects.tranche_cv || !resultat) return;

  let tarifs = [];

  // Valeurs distinctes d'un champ, dans l'ordre d'apparition des données (= ordre voulu par le serveur).
  function valeurs(champ, filtre) {
    const vues = [];
    tarifs.filter(filtre || (() => true)).forEach((t) => { if (!vues.includes(t[champ])) vues.push(t[champ]); });
    return vues;
  }

  function remplir(select, liste) {
    const ancien = select.value;
    select.replaceChildren();
    liste.forEach((v) => {
      const option = document.createElement("option");
      option.value = v;
      option.textContent = v;
      select.appendChild(option);
    });
    if (liste.includes(ancien)) select.value = ancien;
    select.disabled = false;
  }

  function afficher() {
    const choix = tarifs.filter((t) => t.prestation === selects.prestation.value
      && t.categorie === selects.categorie.value && t.tranche_cv === selects.tranche_cv.value);
    const montant = (r) => { const t = choix.find((x) => x.resultat === r); return t ? t.montant_dh + " DH" : "n/c"; };
    resultat.textContent = "Contrôle favorable : " + montant("Favorable") + "  ·  Défavorable : " + montant("Défavorable");
  }

  function majCategories() {
    remplir(selects.categorie, valeurs("categorie", (t) => t.prestation === selects.prestation.value));
    majCv();
  }
  function majCv() {
    remplir(selects.tranche_cv, valeurs("tranche_cv", (t) => t.prestation === selects.prestation.value
      && t.categorie === selects.categorie.value));
    afficher();
  }

  fetch("/api/tarifs", { headers: { Accept: "application/json" } })
    .then((r) => { if (!r.ok) throw new Error("HTTP " + r.status); return r.json(); })
    .then((donnees) => {
      tarifs = donnees;
      remplir(selects.prestation, valeurs("prestation"));
      majCategories();
    })
    .catch(() => {
      Object.values(selects).forEach((s) => s.replaceChildren());
      resultat.textContent = "Tarifs indisponibles pour le moment. Consultez les grilles ci-dessus.";
    });

  selects.prestation.addEventListener("change", majCategories);
  selects.categorie.addEventListener("change", majCv);
  selects.tranche_cv.addEventListener("change", afficher);
})();
