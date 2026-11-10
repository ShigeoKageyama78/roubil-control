// Simulateur de tarif.
// Récupère les tarifs actuels via l'API (/api/tarifs, JSON) puis calcule le montant
// dans le navigateur. Le texte est inséré avec textContent (jamais innerHTML),
// ce qui empêche toute injection de code même si une donnée contenait du HTML.
(function () {
  "use strict";
  const select = document.getElementById("sim-prestation");
  const contre = document.getElementById("sim-contre");
  const resultat = document.getElementById("sim-resultat");
  if (!select || !contre || !resultat) return;

  let tarifs = [];

  function afficher() {
    const choix = tarifs.find((t) => String(t.id) === select.value);
    if (!choix) { resultat.textContent = ""; return; }
    if (contre.checked) {
      const cv = tarifs.find((t) => t.est_contre_visite);
      resultat.textContent = cv
        ? "Contre-visite : " + cv.montant_dh + " DH"
        : "Contre-visite : contactez le centre.";
      return;
    }
    resultat.textContent = choix.nom + " : " + choix.montant_dh + " DH";
  }

  fetch("/api/tarifs", { headers: { Accept: "application/json" } })
    .then((r) => { if (!r.ok) throw new Error("HTTP " + r.status); return r.json(); })
    .then((donnees) => {
      tarifs = donnees;
      select.replaceChildren();
      donnees.filter((t) => !t.est_contre_visite).forEach((t) => {
        const option = document.createElement("option");
        option.value = t.id;
        option.textContent = t.nom + " (" + t.vehicule + ")";
        select.appendChild(option);
      });
      select.disabled = false;
      afficher();
    })
    .catch(() => {
      select.replaceChildren();
      resultat.textContent = "Tarifs indisponibles pour le moment. Consultez la liste ci-dessus.";
    });

  select.addEventListener("change", afficher);
  contre.addEventListener("change", afficher);
})();
