// Validation du formulaire de contact côté navigateur : confort de l'utilisateur uniquement.
// La vraie validation reste faite par le serveur (voir app/validation.py).
(function () {
  "use strict";
  const form = document.getElementById("form-contact");
  if (!form) return;
  form.addEventListener("submit", (e) => {
    form.querySelectorAll(".erreur-js").forEach((n) => n.remove());
    const regles = [
      ["nom", (v) => v.trim().length >= 2, "Entrez votre nom (2 caractères minimum)."],
      ["telephone", (v) => (v.match(/\d/g) || []).length >= 8, "Entrez un numéro de téléphone valide."],
      ["contenu", (v) => v.trim().length >= 10, "Votre message doit faire au moins 10 caractères."],
    ];
    let bloque = false;
    regles.forEach(([id, ok, msg]) => {
      const champ = document.getElementById(id);
      if (!ok(champ.value)) {
        const p = document.createElement("p");
        p.className = "erreur erreur-js";
        p.setAttribute("role", "alert");
        p.textContent = msg;
        champ.insertAdjacentElement("afterend", p);
        bloque = true;
      }
    });
    if (bloque) e.preventDefault();
  });
})();
