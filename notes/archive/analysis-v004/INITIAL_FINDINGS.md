# Wstępne ustalenia (eksploracyjne, jedna sesja, 2026-10-09…16)

Liczone skryptami z `notes/analysis-v004/` (nie kodem raportującym z repo). Referencja = S5 (`p3net_cascade`).
Traktuj jako hipotezy do weryfikacji, nie jako fakty.

- S5 bije random search w 10/16 komórek (seedy 31–60, primary), 8/16 (seedy 1–30), 11/16 (FCNet), nigdy gorszy; S4 (`p3net`, v0.0.3) 0/16.
- Udział bootstrapu przy b=350: S4 ~90–93%, S5 18–45% (primary), 55–60% (FCNet).
- Q1: S5 ~5. miejsce z 23 na primary (seedy 31–60, średni ranking 7.8); przegrywa głównie z SH-EMOA, TPE, BANANAS (po 3 komórki);
  wygrywa z MO-LS, P3-alone, MO-BOHB, RS, REINFORCE; vs NSGANetV2 3+/0−.
- FCNet: S5 ~16. miejsce; kanoniczne P3 (`canonical_p3_scalar_fihc`, `przewozniczek_p3elympus`, `bartnik_p3`) w czołówce (ranking ~3–7).
- Rodzina P3 a typ problemu: na JAHS najlepszy w rodzinie S5; na NAS-HPO-II i FCNet kanoniczne P3; na NB201 różnice minimalne (mediany 0.992–0.996).
- GP (b=50/100): Vizier najlepszy ze wszystkich na NAS-HPO-II i FCNet (ranking 1.0), średni na JAHS (~11); ~14–18 min/przebieg przy b=100;
  BoTorch ≈ S5 jakościowo (remis we wszystkich komórkach), 3–40× droższy. Przy b=50/100 S5 wypada słabiej (~12. na JAHS) niż przy wszystkich budżetach.
- Koszt (s9, b=350): S5 ~135–186 s na JAHS, ~27 s NAS-HPO; kanoniczne P3 ~1100–1300 s (JAHS); GP 1–3.4 h, Vizier do ~30 GB RAM.
  S5 ≈ jakość kanonicznego P3 na primary przy 6–32× mniejszym koszcie. SH-EMOA/NSGA-Net bywają i lepsze, i szybsze (~10 s).
  Wszystkie metody poza GP ~1.5–1.8 GB RAM (S5 najwięcej w tej grupie).
- Q2: S1→S2→S3→S4 bez istotnych zmian (0/16); S4→S5 poprawa 6/16 (primary), 7/16 (FCNet); S4′ (eager mixing) lepsze od S4 w 6/16 —
  sprzeczne z tekstem v0.0.3 („regressed severely”).
- Q3: 16 wariantów ≈ S5, poza `grow_on_stall` (S5 lepszy w 8/16) i `kappa1_thr0` (1 komórka); `inherited_cost` ≈ S5 w 16/16.
- Q4, drabinka S5 → RF (`p3net_bartnik`) → RF+FIHC (`p3net_bartnik_fihc`) → RF+FIHC-eLyMPuS (`p3net_elympus`):
  sam krok eLyMPuS 0/32 istotnych różnic; RF→RF+FIHC: 10/16 lepiej na FCNet. RF przewiduje lepiej (Spearman pred/true ~0.8–0.95 vs ~0.3–0.4 S5),
  ale akceptacja i FIHC po samym f1 przesuwają wyszukiwanie ku dokładnym, drogim modelom (mediana f2 ocenionych punktów +10–65%,
  najlepsze f1 −2…−24%) → pomaga na FCNet, szkodzi na JAHS/NAS-HPO.
  Hipoteza: przewaga S5 na JAHS częściowo bierze się stąd, że jego prawie losowy surogat lepiej pokrywa front po osi kosztu.
  Założenie niesprawdzone: `surrogate_quality_log` zawiera tylko zaakceptowane i ocenione kandydatury.
- eLyMPuS w P3Net i w `przewozniczek_p3elympus` pyta random forest (`fitness_fn = surrogate.predict`), więc jego mechanizm oszczędzania ewaluacji
  nie jest testowany. W P3Net FIHC i FIHC-eLyMPuS dostają tę samą skalarną funkcję f1 → porównanie M8 vs kontrola jest czyste co do celu.
- NB201 przy b=350: od RS odróżniają się S5, RF, RF+eLyMPuS, przewozniczek, canonical, MO-LS; nie: S4, bartnik_p3. Przy b=100 — żadne.
- Q7: ASHA bije S5 w 8/16 (seedy 31–60); Hyperband/BOHB przeważnie przegrywają z S5.
- MOEA/D często nie zużywa budżetu na FCNet/NAS-HPO (np. 46–81 ewaluacji zamiast 350).
- Ryzyko dopasowania: seedy 31–60 wykluczają dopasowanie do seedów (wynik nie spada), nie do benchmarku; spadek S5 na FCNet zgodny albo
  z dopasowaniem do benchmarku, albo z ograniczeniem addytywnego surogatu (proxy interakcji v0.0.3: Fashion +0.016 … NAS-HPO +0.259) — nierozstrzygnięte.
