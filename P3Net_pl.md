# P3Net: Połączenie Bezparametrowej Piramidy Populacji z Predyktorem Zastępczym w Przeszukiwaniu Architektur Sieci Neuronowych

**Autorzy:**

1. Jędrzej Tomasz Polaczek — nazwa wydziału (afiliacja), nazwa organizacji (afiliacja), Szczecin, Polska, jedrzej.polaczek@gmail.com
2. Imię Nazwisko — nazwa wydziału (afiliacja), nazwa organizacji (afiliacja), Miasto, Kraj, adres e-mail lub ORCID

---

## Streszczenie

*(TODO — do uzupełnienia)*

**Słowa kluczowe:** przeszukiwanie architektur sieci neuronowych, predyktor zastępczy, P3, optymalizacja ewolucyjna, optymalizacja wielokryterialna

---

## Wprowadzenie

Przeszukiwanie architektur sieci neuronowych (NAS) eksploruje duże, dyskretne przestrzenie projektów sieci; ocena pojedynczego kandydata stanowi dominujący koszt przeszukiwania. Powszechną praktyką jest dzielenie przeszukiwania na dwa etapy: najpierw architektura przy domyślnych hiperparametrach, potem strojenie hiperparametrów dla zwycięzcy. Zela i in. \citep{zela2018towards} pokazują, że to zawodne z dwóch powodów: architektura i hiperparametry wzajemnie oddziałują, więc najlepsza architektura dla jednego zestawu hiperparametrów nie musi być najlepsza dla innego, a ranking architektur po kilku epokach słabo koreluje z rankingiem przy pełnym budżecie. Rozdzielenie etapów kumuluje oba ryzyka. Wspólne przeszukiwanie obu wymiarów tego unika, kosztem dalszego powiększenia i tak już kosztownej przestrzeni.

NSGA-Net \citep{lu2019nsganet} ustanowił przeszukiwanie ewolucyjne nad architekturami sieci, trenując każdego kandydata do końca. NSGANetV2 \citep{lu2020nsganetv2} pokazał, że ten sam silnik ewolucyjny połączony z wyuczonym predyktorem dokładności pozwala tanio przesiać większość kandydatów, rezerwując pełną ewaluację dla obiecującego podzbioru; wielokryterialna ewolucja architektur sama pozostaje najpopularniejszym podejściem w wielokryterialnym NAS, a wspomaganie predyktorem zastępczym jest jedną z kilku technik efektywności zbudowanych na tym silniku (Prace pokrewne).

Autorzy NSGA-Net dokumentują, że 60–80% wygenerowanych genotypów dekoduje się do zduplikowanych architektur w miarę wzrostu liczby węzłów \citep{lu2019nsganet}. To dowód, że zmienne w kodowaniu wzajemnie oddziałują w sposób, który operator niewidzący tej struktury wykorzysta co najwyżej przypadkowo. Koszt zduplikowanych architektur da się jednak zniwelować środkami inżynierskimi, niezależnymi od samego algorytmu przeszukiwania: wykrywaniem i pomijaniem już widzianych genotypów, stosowanym zarówno przy budowie benchmarków (kanonizacja izomorficznych komórek, jak w NAS-Bench-101 \citep{ying2019nasbench101}), jak i na bieżąco w trakcie przeszukiwania (NSGA-Net, a także P3Net przez własny cache deduplikacji, sekcja Proponowany Optymalizator); to standard od 2019 roku. To rozwiązanie nie jest jednak powszechne. NAS-Bench-201 \citep{dong2020nasbench201}, benchmark z odrębną przestrzenią komórki, nie kanonizuje izomorficznych architektur: jego autorzy wprost przyznają, że budowali go "bez uwzględnienia izomorfizmu", a z 15625 surowych kodowań tylko 6466 (~41%) jest topologicznie unikalnych, co daje wskaźnik duplikacji ~59%. Ta sama, niezniwelowana redundancja trafia więc wprost do JAHS-Bench-201 \citep{bansal2022jahsbench}, zbudowanego na przestrzeni komórki NAS-Bench-201 i będącego jednym z dwóch głównych benchmarków tej pracy (Wyniki). Otwarte pozostaje więc nie samo istnienie duplikatów, lecz węższe pytanie: czy operator przeszukiwania świadomy zależności zmiennych generuje ich mniej już przy proponowaniu kandydatów, zamiast tylko taniej wykrywać je po fakcie.

Właśnie w tę strukturę zależności między zmiennymi genotypu celuje osobny nurt badań: ewolucyjne algorytmy uczące powiązania (linkage learning), takie jak GOMEA \citep{thierens2011optimal} oraz Bezparametrowa Piramida Populacji (P3) \citep{goldman2014parameterless}, rozwijane niezależnie od tej linii badań NAS. Uczą się, które zmienne genotypu oddziałują, i chronią te grupy podczas krzyżowania, zamiast traktować genotyp jako nieustrukturyzowane kodowanie. W zamyśle pozwala to uniknąć redundantnego, generującego duplikaty przeszukiwania, jakie dokumentują wyniki NSGA-Net. Duplikaty i zależności między zmiennymi to jednak dwa różne zjawiska, które nie muszą iść w parze. Duplikaty powstają na etapie dekodowania: różne genotypy mogą opisywać dokładnie tę samą architekturę, niezależnie od tego, jak zmienne wpływają na dopasowanie. Zależności między zmiennymi to coś innego: to, które zmienne genotypu wspólnie decydują o wartości celu. Taki operator uczy się właśnie tych zależności, nie duplikatów. Czy dzięki temu przy okazji generuje też mniej duplikatów, zależy od tego, czy oba zjawiska w praktyce się pokrywają, czyli czy te same grupy zmiennych, które powodują redundancję dekodowania, są też grupami istotnymi dla dopasowania. To właśnie sprawdza diagnostyka wskaźnika duplikacji w sekcji Wyniki.

P3Net łączy dwa elementy: silnik przeszukiwania świadomy struktury zależności i relatywny predyktor zastępczy świadomy tej samej struktury. Silnikiem jest P3, który zastępuje NSGA-II, dzięki czemu krzyżowanie podąża za drzewem powiązań wyuczonym na populacji zamiast działać na pojedynczych zmiennych. Predyktor, zamiast regresji bezwzględnej dokładności kandydata z jego pełnego kodowania, przewiduje zmianę dokładności względem rodzica, ograniczoną do jednego zmodyfikowanego podzbioru powiązań, w duchu eLyMPuS. eLyMPuS jest wariantem LyMPuS \citep{przewozniczek2026lympus} i przewiduje względną zmianę dopasowania wzdłuż struktury powiązań odkrywanej przyrostowo, a nie zakładanej z góry (rozwinięcie w Pracach pokrewnych). Silnik przeszukiwania i predyktor zastępczy są rozszerzone do ustawienia wspólnego, w którym genotyp obejmuje, obok wyborów architektonicznych, hiperparametry treningowe takie jak współczynnik uczenia i zanik wag.

Pytanie badawcze i wkład pracy: czy przy ustalonym, ograniczonym budżecie pełnych ewaluacji przeszukiwanie P3 świadome zależności, połączone z relatywnym predyktorem zastępczym świadomym struktury powiązań, daje kandydatów o lepszym kompromisie dokładność–koszt niż selekcja NSGA-II oparta na odległości zagęszczenia, połączona z bezwzględnym predyktorem regresyjnym jak w NSGANetV2? Testujemy to w ustawieniu wspólnego przeszukiwania architektury i hiperparametrów. Dopasowane badania ablacyjne rozdzielają obie dźwignie, silnik i predyktor, na tyle, na ile pozwala konstrukcja eksperymentu; relatywny predyktor zastępczy jest zdefiniowany wyłącznie przy danym drzewie powiązań, więc nie może zostać połączony z NSGA-II, a sekcja Wyniki omawia to ograniczenie. Odpowiadamy na to pytanie za pomocą P3Net: ewolucyjnego algorytmu uczącego powiązania połączonego z relatywnym predyktorem zastępczym do wspólnego przeszukiwania architektury i hiperparametrów, na dwóch benchmarkach, JAHS-Bench-201 i NAS-HPO-Bench-II, przy równych budżetach pełnych ewaluacji. Oceniamy go przez kontrolowane porównanie z NSGANetV2, tymi ablacjami oraz SH-EMOA i MO-BOHB, metodami odniesienia ustanowionymi właśnie dla tego ustawienia wspólnego na tych samych dwóch benchmarkach \citep{guerreroviu2021bagofbaselines}. Najbliższa wcześniejsza praca już łączy algorytm uczący powiązania z predyktorem zastępczym w przeszukiwaniu sieci, lecz tylko w przestrzeni architektury \citep{bartnik2026evolutionary}; sekcja Prace pokrewne omawia, czym P3Net różni się od tego punktu odniesienia: relatywnym predyktorem świadomym struktury powiązań, bezpośrednim porównaniem z NSGA-II/NSGANetV2 oraz zakresem obejmującym architekturę i hiperparametry wspólnie.

---

## Prace pokrewne

Przeszukiwanie ewolucyjne architektur bez wspomagania predyktorem zastępczym zapoczątkował NSGA-Net \citep{lu2019nsganet}, wykorzystujący NSGA-II jako silnik przeszukiwania architektur sieci konwolucyjnych, z selekcją opartą na sortowaniu niezdominowanym i odległości zagęszczenia. Każdy kandydat przechodzi pełny trening; jedynym mechanizmem przyspieszającym zbieżność jest wykorzystanie historii przeszukiwania przez sieć bayesowską. Autorzy dokumentują też znaczącą redundancję na drodze od genotypu do fenotypu: 60–80% wygenerowanych genotypów odpowiada zduplikowanym architekturom w miarę wzrostu liczby węzłów, co wskazuje na nietrywialną, nieliniową strukturę zależności ukrytą w kodowaniu architektury.

Rok później NSGANetV2 \citep{lu2020nsganetv2} wprowadził predyktor dokładności doskonalony na bieżąco i zastąpił pełny trening od zera dostrajaniem wag odziedziczonych z supersieci, zmniejszając liczbę w pełni ewaluowanych architektur do 350 (Tabela 2 oryginału). Zamiana ta wymienia koszt treningu na udokumentowane ryzyko niezgodności rankingów między dokładnością przy współdzieleniu wag a dokładnością z niezależnego treningu \citep{yu2020evaluatingnas}. Ten schemat kontynuuje wzorzec, który przeglądy literatury wskazują jako najpopularniejsze podejście w wielokryterialnym NAS: ewolucję architektur za pomocą wielokryterialnego algorytmu ewolucyjnego, czego przykładem jest tam wprost przywoływany NSGANetV2 \citep{white2023insights}. Połączenie tego silnika z wyuczonym predyktorem zastępczym to uznana technika redukcji kosztu ewaluacji, jedna z kilku obok współdzielenia wag i tanich (zero-cost) predyktorów \citep{liu2023survey}, a nie kombinacja wskazywana przez którykolwiek z tych przeglądów jako jedyny dominujący paradygmat dziedziny. Dalszy rozwój skierował się ku predyktorom opartym na rankingowaniu zamiast regresji, takim jak RankNet w MoSegNAS \citep{lu2022mosegnas}, który rozszerza podejście NSGANetV2 na segmentację semantyczną, a także ku krytycznej ocenie proxy zerokosztowych, których udokumentowaną słabością jest niewiarygodne rozróżnianie architektur na szczycie rankingu.

Równolegle rozwinęła się odrębna rodzina algorytmów ewolucyjnych, jawnie modelująca strukturalne zależności między zmiennymi genotypu: GOMEA \citep{thierens2011optimal} oraz Bezparametrowa Piramida Populacji (P3) \citep{goldman2014parameterless}. Algorytmy te budują drzewo powiązań na podstawie zależności statystycznych obserwowanych w populacji i wykorzystują je do kierowania krzyżowaniem, chroniąc wykryte grupy zależnych zmiennych przed zaburzeniem. P3 dodatkowo przeciwdziała przedwczesnej zbieżności typowej dla modeli generacyjnych: w odróżnieniu od NSGA-II nie odrzuca wcześniej znalezionych dobrych rozwiązań. Strukturalnie zastępuje pojedynczą populację o stałym rozmiarze uporządkowaną piramidą populacji o rosnącym rozmiarze, dodając nowy poziom dopiero gdy istniejące poziomy przestają dawać lepsze rozwiązania. Ta właściwość odpowiada za nazwę „bezparametrowa”: rozmiar populacji nie jest wybierany z góry \citep{goldman2014parameterless}. Awans pojedynczego nowego rozwiązania w górę piramidy w standardowym ujęciu wymaga rzeczywistej ewaluacji dopasowania przy każdej zaakceptowanej lokalnej poprawie, nie tylko na końcu procesu; ten szczegół ma bezpośrednie znaczenie dla rozliczania budżetu przy niewielkich budżetach P3Net (Wyniki wraca do tego przy ablacji P3 bez predyktora zastępczego).

Opisane powyżej powiązania, uczone statystycznie na poziomie populacji, nie powinny być mylone z optymalizacją gray-box w węższym sensie, ustanowionym przez Whitleya, Chicano i Goldmana \citep{whitley2016graybox} i stosowanym w nurcie prac nad GOMEA, w tym w jego rozszerzeniu rzeczywistoliczbowym RV-GOMEA \citep{andreadis2024maxclique} oraz we wspólnej bibliotece GOMEA \citep{bouter2023library}. Tam optymalizator otrzymuje jawny dostęp do podfunkcji funkcji celu i wykorzystuje ten dostęp do taniej, częściowej ponownej ewaluacji po zlokalizowanej zmianie zmiennej. Niniejsza praca działa w reżimie black-box: dokładności walidacyjnej NAS nie da się rozłożyć na lokalnie przeliczalne podfunkcje, więc P3 pełni tu wyłącznie rolę silnika przeszukiwania świadomego struktury zależności genotypu, a redukcję kosztu osiąga omawiany dalej wyuczony predyktor zastępczy.

Podobnie jak w NSGA-Net i NSGANetV2, koszt pełnej ewaluacji pozostaje głównym wąskim gardłem także dla ewolucyjnych algorytmów uczących powiązania: każdy krok optymalnego mieszania proponuje częściową zmianę zmiennej, której wpływ na funkcję celu musi, w reżimie black-box, zostać zweryfikowany pełną ewaluacją dopasowania. Połączenie tego silnika z tanim, wyuczonym predyktorem zastępczym, który przesiewa kandydatów przed pełną ewaluacją, jest więc naturalnym rozszerzeniem.

Łączenie algorytmów uczących powiązania z wyuczonym predyktorem zastępczym było już badane, choć nie w dziedzinie NAS. CS-GOMEA \citep{dushatskiy2019csgomea} integruje GOMEA z konwolucyjną siecią neuronową jako predyktorem zastępczym, ocenianą na syntetycznych problemach kombinatorycznych (Onemax, funkcje Trap, krajobrazy NK, HIFF); autorzy jawnie wskazują niewykorzystanie informacji z drzewa powiązań przy budowie predyktora jako otwarty kierunek badawczy. Dushatskiy, Alderliesten i Bosman \citep{dushatskiy2021novelsurrogateassistedevolutionaryalgorithm} jako pierwsi integrują predyktor zastępczy bezpośrednio z wariantem P3, testując podejście na kosztownym, rzeczywistym problemie uczenia zespołowego opartego na partycjonowaniu; w ich eksperymentach model SVR przewyższył predyktor neuronowy. Najnowsza praca w tym nurcie, LyMPuS \citep{przewozniczek2026lympus}, wprowadza predyktor zastępczy zintegrowany bezpośrednio z mechanizmem odkrywania powiązań i weryfikuje go w połączeniu z P3, ponownie na klasycznych benchmarkach kombinatorycznych: krajobrazach NK, szkłach spinowych Isinga i Max3Sat. Predyktor zastępczy P3Net opiera się konkretnie na eLyMPuS, „empirycznej” wersji LyMPuS wprowadzonej w tej samej pracy, która zastępuje założenie LyMPuS o znanej prawdziwej strukturze zależności strukturą odkrywaną przyrostowo i potencjalnie niekompletnie, w ustawieniu black-box, dokładnie takim, w jakim działa P3Net. Mechanicznie jednak $\hat{\delta}_F$ regresuje ciągłą różnicę dopasowania, a nie dyskretne porównanie lepszy/gorszy/niejednoznaczny stosowane przez eLyMPuS; to plasuje jej mechanizm obliczeniowy bliżej relatywnego predyktora zastępczego CS-GOMEA \citep{dushatskiy2019csgomea}. Dług wobec eLyMPuS ma charakter filozoficzny (relatywny estymator świadomy struktury powiązań nad niekompletnie odkrytą strukturą), nie mechaniczny, więc P3Net rezygnuje z jej gwarancji odtworzenia zależności, warunkowanej monotonicznością. Sekcja Proponowany Optymalizator szczegółowo opisuje tę adaptację.

Wśród zastosowań algorytmów uczących powiązania bezpośrednio do NAS, które całkowicie rezygnują z wyuczonego predyktora zastępczego, jedyną zidentyfikowaną pracą jest praca Trana, Truonga, Vo i Luonga \citep{tran2023gomeanas}, łącząca GOMEA z Synaptic Flow: metryką nie wymagającą treningu, liczoną analitycznie, bez uczenia się z wcześniejszych ewaluacji. To fundamentalnie odmienny mechanizm redukcji kosztu niż wyuczony predyktor zastępczy i, jak omówiono poniżej, różni się od wspomaganego predyktorem uczenia powiązań, jakie do NAS zastosowała Bartnik \citep{bartnik2026evolutionary}.

Niezależnie od podejść opartych na uczeniu powiązań, węższy nurt prac zajął się wspólną optymalizacją architektury i hiperparametrów treningowych, zamiast traktować strojenie hiperparametrów jako odrębny krok po przeszukiwaniu architektury \citep{zela2018towards}. Od tego czasu wprowadzono ustandaryzowane benchmarki dla tego ustawienia: JAHS-Bench-201 \citep{bansal2022jahsbench}, benchmark oparty na predyktorze zastępczym nad wspólną przestrzenią łączącą zmienne kategoryczne i ciągłe, oraz NAS-HPO-Bench-II \citep{hirose2021nashpobenchii}, tablicę przeglądową opartą na stałej siatce kombinacji architektury i hiperparametrów. Systematyczne porównanie solverów w tym ustawieniu \citep{guerreroviu2021bagofbaselines} ocenia standardowe metody odniesienia, takie jak SH-EMOA (wielokryterialna EA oparta na SMS-EMOA), MO-BOHB oraz przeszukiwanie losowe; żadna z porównywanych metod nie jest ewolucyjnym algorytmem uczącym powiązania. P3Net przejmuje SH-EMOA i MO-BOHB jako dodatkowe metody odniesienia bezpośrednio z tego porównania (Wyniki): w odróżnieniu od NSGANetV2, importowanego z NAS ograniczonego do samej architektury i rozszerzanego tutaj na ustawienie wspólne, SH-EMOA i MO-BOHB zostały ustanowione właśnie dla wspólnego przeszukiwania architektury i hiperparametrów na tych samych dwóch benchmarkach.

W całej literaturze wspólnego NAS+HPO hiperparametryczna połowa przestrzeni dotyczy konsekwentnie procedury treningowej, nie strukturalnej pojemności sieci. JAHS-Bench-201 \citep{bansal2022jahsbench} przeszukuje jako hiperparametry współczynnik uczenia, zanik wag, funkcję aktywacji i augmentację danych; liczba komórek i szerokość kanałów są odrębną osią wierności obok liczby epok i rozdzielczości wejścia. NAS-HPO-Bench-II \citep{hirose2021nashpobenchii} zmienia jako hiperparametry jedynie współczynnik uczenia i rozmiar batcha, na ustalonej topologii komórki; czas treningu obsługuje osobny predyktor zastępczy, nie zmienna przeszukiwana. Zela i in. \citep{zela2018towards} podobnie optymalizują wspólnie kategoryczne metaparametry wielogałęziowej architektury ResNet (liczba bloków resztkowych i gałęzi na blok, współczynnik poszerzenia na blok) razem z siedmioma ciągłymi hiperparametrami treningowymi: początkowym współczynnikiem uczenia, rozmiarem batcha, momentum, zanikiem wag L2, długością CutOut, parametrem $\alpha$ MixUp i częstością ShakeDrop, wykorzystując liczbę epok wyłącznie jako wymiar zasobu w Hyperbandzie. P3Net stosuje tę samą konwencję: rozszerzenie genotypu dla ustawienia wspólnego dodaje hiperparametry procedury treningowej, podczas gdy pojemność strukturalna pozostaje częścią kodowania architektury. Bartnik \citep{bartnik2026evolutionary} omija tę kwestię całkowicie, bo jej genotyp nie ma wymiaru hiperparametrów: procedurę treningową ustala tablica NAS-Bench-201, a jej dyskusja przyznaje, że wnioski opisują tę zamkniętą przestrzeń, nie NAS w ogólności. To ograniczenie motywuje ewaluację na rzeczywiście wspólnych benchmarkach, takich jak wymienione powyżej.

Przeanalizowana literatura różni się też tym, co dostarcza prawdę odniesienia. Zela i in. \citep{zela2018towards} optymalizują ustawienie wspólne przez BOHB na rzeczywistych przebiegach treningowych. NAS-HPO-Bench-II \citep{hirose2021nashpobenchii} i JAHS-Bench-201 \citep{bansal2022jahsbench} odpowiadają na każde zapytanie przez stałą tablicę lub wyuczony predyktor zastępczy, bez treningu w chwili ewaluacji. Benchmarki pierwszego rodzaju, z wyczerpująco enumerowalną tablicą, nad którą można obliczyć dokładny front Pareto, określamy jako *Kategorię 1*; benchmarki drugiego rodzaju, odpowiadające przez wyuczony, ciągły predyktor zastępczy bez enumerowalnego frontu oracle, jako *Kategorię 2*. NAS-HPO-Bench-II należy do Kategorii 1, JAHS-Bench-201 do Kategorii 2. Klasyfikacja NAS-HPO-Bench-II jako Kategorii 1 zakłada, że P3Net odpytuje wyłącznie jego wyczerpująco stablicowany zakres (do 12 epok treningu, z trzema zarejestrowanymi ziarnami na wpis); sam benchmark udostępnia też osobny, wyuczony surogat (sieć GIN połączona z MLP) ekstrapolujący wyniki do 200 epok, który, gdyby stanowił poziom pełnej ewaluacji $r_K$, podważałby tę klasyfikację i status frontu oracle. Poziom $r_K$ P3Net dla tego benchmarku jest ustalony wyłącznie na zakresie stablicowanym (do 12 epok); 200-epokowa ekstrapolacja surogatu nigdy nie jest odpytywana przez pętlę przeszukiwania, więc klasyfikacja Kategorii 1 i status frontu oracle są zachowane. Główne benchmarki P3Net to właśnie te dwa, wybrane z powodów już ustalonych w tym nurcie i szerzej w literaturze NAS Kategorii 1: deterministyczna funkcja celu, obliczalny front oracle, ograniczony budżet ewaluacji.

Ten predyktor zastępczy na poziomie benchmarku nie powinien być mylony z wyuczonym predyktorem, który P3Net, CS-GOMEA \citep{dushatskiy2019csgomea}, Dushatskiy i in. \citep{dushatskiy2021novelsurrogateassistedevolutionaryalgorithm} oraz LyMPuS \citep{przewozniczek2026lympus} budują w trakcie przeszukiwania. Predyktor JAHS-Bench-201 zastępuje funkcję celu raz, offline, przed przeszukiwaniem; predyktor działający w czasie przeszukiwania jest dopasowywany przyrostowo, wyłącznie by decydować, którzy kandydaci zasługują na pełne zapytanie. To niezależne decyzje projektowe; wkład P3Net dotyczy wyłącznie drugiej, nałożonej na dowolne podłoże odpowiadające za pełną ewaluację.

Najbliższa niniejszej pracy jest praca Bartnik \citep{bartnik2026evolutionary}, adaptująca SA-P3-GOMEA (algorytm uczący powiązania wspomagany predyktorem zastępczym) do wielokryterialnego NAS na NAS-Bench-201, optymalizując dokładność walidacyjną względem zmierzonego zużycia energii GPU. Zastosowany tam predyktor jest bezwzględnym regresorem nad płaskim genotypem (deterministyczne lub probabilistyczne warianty SVR, MLP, lasu losowego, gradient boostingu); metodami odniesienia są MO-LS i pozbawiony predyktora MO-P3-GOMEA, nie NSGA-II czy NSGANetV2; przestrzeń przeszukiwania to zamknięty benchmark NAS-Bench-201 ograniczony do architektury, bez hiperparametrów treningowych w genotypie.

Trzy niezależne systematyczne przeglądy ewolucyjnego NAS \citep{liu2023survey, white2023insights, ozcelik2026survey} nie wymieniają GOMEA, P3 ani uczenia powiązań jako odrębnej kategorii metod, co wskazuje, że ta rodzina pozostaje poza głównym nurtem dziedziny. Połączenie ewolucyjnego algorytmu uczącego powiązania z wyuczonym predyktorem zostało już zweryfikowane empirycznie, a praca Bartnik rozszerza je na NAS. Cztery aspekty pozostają jednak wspólnie nierozwiązane: relatywny predyktor zastępczy świadomy struktury powiązań zamiast bezwzględnego regresora nad płaskim genotypem; NSGA-II/NSGANetV2 jako bezpośrednio porównywana metoda odniesienia; wspólne przeszukiwanie architektury i hiperparametrów, do którego, zgodnie z naszą wiedzą, żaden ewolucyjny algorytm uczący powiązania nie był wcześniej stosowany; oraz wpływ świadomości powiązań na wskaźnik duplikatów genotypu w przestrzeni typu graf-komórka. Nawet Bartnik, jedyna dotychczasowa praca z tej linii operująca na takiej przestrzeni (NAS-Bench-201, podatnej na ten sam izomorfizm co omówiony we Wprowadzeniu JAHS-Bench-201), nie raportuje tego wskaźnika jako odrębnej diagnostyki.

---

## Sformułowanie Problemu

### Definicja formalna

Niech $[n] \triangleq \{1, \dots, n\}$.
Przestrzeń przeszukiwania definiujemy jako iloczyn kartezjański
\[
    \Lambda = \Lambda_1 \times \Lambda_2 \times \cdots \times \Lambda_n,
\]
gdzie każde $\Lambda_i$ jest skończonym zbiorem operacji (np.\ \textsc{conv}$3{\times}3$, \textsc{skip}, \textsc{none}).
Genotyp $x = (x_1, \dots, x_n) \in \Lambda$ przypisuje jedną operację każdej krawędzi grafu komórki.
W ustawieniu wspólnego przeszukiwania architektury i hiperparametrów, na którym skupia się sekcja Wyniki, $\Lambda$
jest rozszerzona o ciągłe współrzędne hiperparametrów treningowych (np.\ współczynnik uczenia, zanik wag),
co daje $\Lambda = \Lambda_1 \times \cdots \times \Lambda_n \times \Theta$, gdzie $\Theta \subset \mathbb{R}^m$
gromadzi te współrzędne. Otwarte pozostają dwa sposoby obsługi $\Theta$ przez blokowe krzyżowanie P3 oparte na
drzewie powiązań, zdefiniowane nad dyskretnymi grupami; oba są zgodne z poniższym sformułowaniem: (i) dyskretyzacja
każdej współrzędnej $\Theta$ do zbioru skończonego, wchłaniająca ją do powyższego iloczynu bez zmiany operatora
krzyżowania, lub (ii) rozszerzenie drzewa powiązań i optymalnego mieszania o mieszanie rzeczywistoliczbowe na
$\Theta$ w duchu RV-GOMEA \citep{andreadis2024maxclique}, obok dyskretnego mieszania na $\Lambda_1 \times \cdots
\times \Lambda_n$. Wybór jednego z tych podejść ustalamy jednorazowo w sekcji Proponowany Optymalizator; żaden nie
zmienia zdefiniowanych poniżej $D$, $g$, $f_1$ ani $f_2$.

**Dekodowanie i poprawność.**
Funkcja dekodująca $D \colon \Lambda \to \mathcal{N}$ odwzorowuje genotyp na sieć neuronową.
Nie każdy genotyp daje w wyniku poprawną architekturę (np.\ nie istnieje ścieżka między wejściem a wyjściem komórki).
Ograniczenie poprawności wyrażamy jako
\[
    g(x) \leq 0,
\]
gdzie $g \colon \Lambda \to \mathbb{R}$ jest funkcją strukturalną, w tej pracy boolowską
(np.\ $g(x) \in \{-1, +1\}$ koduje istnienie ścieżki wejście–wyjście), zapisaną jednak w postaci rzeczywistoliczbowej,
by uwzględnić stopniowaną miarę niedopuszczalności, gdyby jakiś benchmark taką definiował. $x$ jest *poprawny*
wtedy i tylko wtedy, gdy $g(x) \leq 0$.
Zbiór poprawnych genotypów oznaczamy jako $\Lambda^* = \{x \in \Lambda : g(x) \leq 0\}$.

**Funkcje celu.**
Każdy genotyp $x \in \Lambda^*$ jest oceniany za pomocą dwóch funkcji:
\begin{align}
    f_1(x) &= \text{błąd walidacyjny sieci } D(x) \quad \text{(minimalizowany)}, \\
    f_2(x) &= \phi\bigl(D(x)\bigr) \quad \text{(proxy kosztu obliczeniowego, minimalizowane)},
\end{align}
gdzie $\phi$ oznacza wybraną miarę kosztu obliczeniowego (liczbę parametrów lub FLOP-y), obliczaną analitycznie
dla ustalonej rozdzielczości wejścia, utrzymywanej na poziomie rozdzielczości ustalonym przez najwyższy poziom
wierności $r_K$ (Ewaluacja wielopoziomowa, poniżej), tak aby $f_2$ nie zmieniało się w zależności od poziomu wierności,
przy którym akurat odpytywane jest $f_1$, nawet na benchmarkach takich jak JAHS-Bench-201, gdzie sama rozdzielczość
jest jedną z osi wierności.

**Sformułowanie wielokryterialne.**
Poszukujemy zbioru rozwiązań niezdominowanych (frontu Pareto):
\[
    \begin{aligned}[t]
        \mathcal{P}^* ={} & \bigl\{ x \in \Lambda^* : \nexists\, x' \in \Lambda^*,\; \\
        & f_1(x') \leq f_1(x) \;\wedge\; f_2(x') \leq f_2(x) \;\wedge{} \\
        & \mathbf{f}(x') \neq \mathbf{f}(x) \bigr\},
    \end{aligned}
\]
gdzie $\mathbf{f}(x) = (f_1(x), f_2(x))$.

**Ewaluacja wielopoziomowa (multi-fidelity).**
Ewaluacja $f_1(x)$ przy pełnej wierności jest kosztowna. Wprowadzamy drabinę wierności $r_1 < r_2 < \cdots < r_K$,
uporządkowaną według rosnącej liczby epok treningu; tam, gdzie benchmark udostępnia dodatkowe osie zasobów wpływające
na koszt ewaluacji lub proxy obliczeniowe (np.\ rozdzielczość wejścia), każdy poziom $r_k$ dodatkowo ustala odpowiednie
ustawienie na tych osiach, tak że $r_k$ oznacza pełną konfigurację zasobów, a nie samą liczbę epok. Na benchmarkach
z pojedynczą osią zasobów sprowadza się to do tego, że $r_k$ oznacza wyłącznie liczbę epok treningu.
Funkcja celu na poziomie $r_k$ to $f_1^{(k)}(x)$; wartość na najwyższym poziomie $f_1^{(K)}(x)$ jest docelową miarą
jakości. Do uczenia i selekcji modelu metody wykorzystujące drabinę wierności używają $f_1^{(k)}(x)$ na najniższym
poziomie, który wystarczająco koreluje z $f_1^{(K)}(x)$, zapobiegając obciążeniu wprowadzanemu przez mieszanie
poziomów wierności; sam P3Net nie wykorzystuje tej drabiny, działając wyłącznie na poziomie $r_K$ (Proponowany
Optymalizator). Żadna z metod porównywanych w sekcji Wyniki (Metody odniesienia) również jej nie wykorzystuje.
Definiujemy ją tutaj jako ogólny mechanizm na poziomie podłoża, przydatny, gdyby do porównania miała
w przyszłości dołączyć metoda odniesienia wielopoziomowa (np.\ oparta na Hyperbandzie), lecz nie jako aktywny
składnik obecnego eksperymentu.

**Szum ewaluacji.**
Tam, gdzie podłoże odpowiadające za $f_1$ niesie ze sobą rzeczywistą stochastyczność, na przykład rzeczywisty trening
lub własne zarejestrowane powtórzenia benchmarku, $f_1^{(k)}(x)$ jest traktowane jako zmienna losowa: każda
konfiguracja jest ewaluowana z użyciem $s$ różnych ziaren losowości (seedów) lub próbek pobranych z zarejestrowanych
powtórzeń podłoża, a do selekcji i raportowania wykorzystywana jest mediana z nich. Podłoża deterministyczne, takie
jak predyktor zastępczy dający pojedynczy punktowy estymat, nie wymagają takiego uśredniania. Oba główne benchmarki
P3Net (Wyniki) odpowiadają na zapytania deterministycznie: predyktor zastępczy dający pojedynczy estymat dla
JAHS-Bench-201, stała tablica przeglądowa dla NAS-HPO-Bench-II w zakresie stablicowanym wyczerpująco (zastrzeżenie co do
poziomu wierności $r_K$ dla tego benchmarku omawia sekcja Prace pokrewne). W całej tej pracy $s=1$, a ten krok uśredniania
nie jest wykorzystywany; jest zachowany jako ogólny mechanizm na poziomie podłoża z myślą o przyszłych pracach nad
podłożami stochastycznymi, takimi jak rzeczywisty trening. $s$ nie należy mylić z $R$, liczbą niezależnych przebiegów
przeszukiwania na metodę (Wyniki): $R$ pozostaje istotne niezależnie od determinizmu podłoża, bo losowość między
przebiegami wynika z inicjalizacji i stochastycznych operatorów przeszukiwania, nie z powtarzanych zapytań o tę samą
konfigurację.

**Model predyktora zastępczego.**
Pełna ewaluacja $f_1(x)$ odpytuje prawdziwą funkcję celu dla $D(x)$; konkretne podłoże tego zapytania, czy to
rzeczywisty trening, tablica przeglądowa benchmarku, czy własny predyktor zastępczy benchmarku, jest skonkretyzowane
w sekcji Wyniki. Po zebraniu $t$ pełnych ewaluacji dysponujemy zbiorem obserwacji
\[
    \mathcal{H}_t = \bigl\{ (x^{(i)},\, \mathbf{f}(x^{(i)})) \bigr\}_{i=1}^{t}.
\]
Zamiast regresować $f_1$ bezpośrednio z zakodowanego genotypu, jak w NSGANetV2, predyktor zastępczy stosowany przez
P3Net jest *relatywny* i *świadomy struktury powiązań*: dla rodzica $x \in \Lambda^*$ i kandydata $x'$
różniącego się od $x$ wyłącznie na współrzędnych podzbioru powiązań $F \subseteq [n]$ zidentyfikowanego przez bieżący
model zależności (tj.\ $x'_i = x_i$ dla wszystkich $i \notin F$), predyktor zastępczy przewiduje efekt tej lokalnej
zmiany względem rodzica,
\[
    \hat{\delta}_F \colon \Lambda^* \times \Lambda^* \to \mathbb{R},
    \quad
    \hat{\delta}_F(x, x') \approx f_1(x) - f_1(x'),
\]
wytrenowany na parowych różnicach dopasowania (fitness) wyprowadzonych z $\mathcal{H}_t$.
Podstawowy koszt przeszukiwania mierzony jest liczbą wywołań $f_1$ (pełnych ewaluacji), a nie liczbą wywołań
$\hat{\delta}_F$. To właśnie odróżnia P3Net od NSGANetV2 już na poziomie sformułowania problemu: P3Net ocenia
kandydatów względem ich rodzica, wykorzystując strukturę odkrytą przez P3, podczas gdy NSGANetV2 ocenia każdego
kandydata w kategoriach bezwzględnych wyłącznie na podstawie jego kodowania.
Konstrukcja i aktualizacja $\hat{\delta}_F$ oraz jej wykorzystanie w pętli przeszukiwania P3Net są opisane w sekcji
Proponowany Optymalizator.

---

## Proponowany Optymalizator

**Reprezentacja i drzewo powiązań.** Drzewo powiązań budowane jest na podstawie bieżącej populacji i odzwierciedla zależności statystyczne między zmiennymi genotypu: wyborami operacji na poszczególnych krawędziach z sekcji Sformułowanie Problemu, rozszerzonymi poniżej o zdyskretyzowane współrzędne $\Theta$, gdy w grę wchodzi ustawienie wspólne. Zgodnie ze standardową procedurą P3, drzewo konstruowane jest za pomocą aglomeracyjnego grupowania hierarchicznego w stylu UPGMA nad znormalizowaną miarą zależności opartą na informacji wzajemnej między zmiennymi genotypu, dając zagnieżdżoną rodzinę podzbiorów zmiennych wykorzystywaną przez operator optymalnego mieszania; konstrukcja ta jest stosowana do genotypu NAS bez zmian względem jego pierwotnej postaci optymalizacji kombinatorycznej. P3Net przyjmuje opcję (i) z sekcji Sformułowanie Problemu: każda ciągła współrzędna $\Theta$ jest dyskretyzowana do skończonego zbioru przedziałów (binów), ustalonego jednorazowo przed rozpoczęciem przeszukiwania (np.\ siatka logarytmiczna dla współczynnika uczenia), tak że wspólny genotyp $\Lambda_1 \times \cdots \times \Lambda_n \times \Theta$ jest w całości kategoryczny, a drzewo powiązań, jego oparta na informacji wzajemnej miara zależności oraz opisane poniżej przemiatanie optymalnego mieszania stosują się do niego dokładnie tak samo, jak do kodowania obejmującego wyłącznie architekturę, bez odrębnego mechanizmu mieszania rzeczywistoliczbowego. Takie podejście wymienia rozdzielczość ciągłego przeszukiwania hiperparametrów na utrzymanie centralnego porównania z NSGA-II/NSGANetV2 przypisywalnego wyłącznie silnikowi przeszukiwania i predyktorowi zastępczemu, zamiast mieszać je z dodatkowym, odrębnie nowatorskim rozszerzeniem P3 o mieszanie rzeczywistoliczbowe; rozszerzenie do opcji (ii) (mieszanie rzeczywistoliczbowe w duchu RV-GOMEA \citep{andreadis2024maxclique}) pozostawiono jako przyszłą pracę.

**Krzyżowanie.** Krzyżowanie działa na poziomie grup zmiennych zidentyfikowanych przez to drzewo, a nie na poziomie pojedynczych bitów, chroniąc wykryte grupy powiązanych decyzji projektowych przed zaburzeniem.

**Brak operatora mutacji.** P3Net, podobnie jak cała linia P3/GOMEA, z której korzysta \citep{goldman2014parameterless,thierens2011optimal}, nie ma osobnego kroku mutacji: cała wariacja powstaje w wyniku sterowanego drzewem powiązań przemiatania optymalnego mieszania opisanego poniżej, więc różnorodność populacji pochodzi wyłącznie z rekombinacji względem drzewa powiązań, a nie z dodatkowego operatora losowej perturbacji.

**Predyktor zastępczy.** Konstrukcja predyktora zastępczego w P3Net wykorzystuje tę samą strukturę zależności, która kieruje operatorem wariacji: relatywny estymator $\hat{\delta}_F$ świadomy struktury powiązań, zdefiniowany w sekcji Sformułowanie Problemu, wytrenowany na parowych różnicach dopasowania wyprowadzonych z $\mathcal{H}_t$, jest tym, co przemiatanie optymalnego mieszania P3 odpytuje przy każdej proponowanej modyfikacji. Mechanicznie ten oparty na regresji estymator jest bliższy relatywnemu predyktorowi zastępczemu CS-GOMEA \citep{dushatskiy2019csgomea} niż dyskretnemu porównaniu eLyMPuS; dług wobec eLyMPuS, wariantu LyMPuS \citep{przewozniczek2026lympus}, ma charakter filozoficzny, nie mechaniczny. Oba przewidują relatywną zmianę dopasowania warunkowaną niekompletnie odkrytą strukturą powiązań, a nie zakładaną jako znaną z góry (rozwinięcie w sekcji Prace pokrewne); w P3Net mechanizm zaadaptowano do kodowania architektury sieci.

**Konstrukcja teleskopowa.** Estymatę bezwzględnego błędu kandydata uzyskuje się kompozycyjnie, poprzez teleskopowe cofnięcie tej relatywnej korekty wzdłuż przemiatania do najbliższego przodka o znanej, w pełni ewaluowanej wartości $f_1$: zapisując $x_0, x_1, \dots, x_m = x'$ jako łańcuch tymczasowo zaakceptowanych modyfikacji od tego przodka $x_0$ (przy znanym $f_1(x_0)$), przy czym każdy krok wnosi $\hat{\delta}_{F_i}(x_{i-1}, x_i)$ dla podzbioru powiązań $F_i$ zmodyfikowanego w kroku $i$,
\[
    \hat{f}_1(x_m) = f_1(x_0) - \sum_{i=1}^{m} \hat{\delta}_{F_i}(x_{i-1}, x_i),
\]
co sprowadza się do $\hat{f}_1(x') = f_1(x) - \hat{\delta}_F(x, x')$ w przypadku pojedynczego kroku $m=1$. Głębokość łańcucha $m$ jest ograniczona przez $\kappa$, wprowadzone poniżej, właśnie po to, by ograniczyć, jak daleko może się propagować skumulowany błąd predyktora zastępczego, zanim zresetuje go pełna ewaluacja.

**Pętla przeszukiwania.** Rysunek poniżej przedstawia jedną iterację schematycznie: dopisek „(z $\mathcal{H}_t$)” oznacza osobnika z rzeczywistą, w pełni ocenioną wartością $f_1$; dopisek „(tymczasowy)” oznacza osobnika zaakceptowanego wyłącznie przez predyktor zastępczy $\hat\delta_F$, jeszcze niepotwierdzonego pełną ewaluacją (w wersji LaTeX, `chapters/v003/proposed_optimizer/main.tex`, to samo rozróżnienie pokazane jest liniami ciągłymi/przerywanymi).

```
  ┌─────────────────────────────────┐
  │ rodzic x  (z H_t)               │
  └───────────────┬─────────────────┘
                  │
                  ▼
  ┌─────────────────────────────────┐
  │ donor → propozycja x' na F      │ (tymczasowy)
  └───────────────┬─────────────────┘
                  │
                  ▼
  ┌─────────────────────────────────┐
  │ ocena: δ̂_F(x, x')               │
  └───────────────┬─────────────────┘
                  │
                  ▼
  ┌─────────────────────────────────┐
  │ δ̂_F ≥ 0? → tymczasowa akceptacja│ (tymczasowy)
  └───────────────┬─────────────────┘
                  │
                  ├── kolejny podzbiór F (pętla, do κ razy) ─────┐
                  │                                              │
                  ▼                                              │
  ┌────────────────────────────────┐                             │
  │ sweep zakończony lub κ         │◀────────────────────────────┘
  │ osiągnięte: wybór C*           │ (niezdominowani w (f̂_1, f_2))
  └───────────────┬────────────────┘
                  │
                  ▼
  ┌────────────────────────────────┐
  │ pełna ewaluacja f_1(x)         │ (z H_t)
  └───────────────┬────────────────┘
                  │
                  ▼
  ┌────────────────────────────────┐
  │ aktualizacja H_t,              │
  │ retrening δ̂_F,                 │
  │ przebudowa drzewa powiązań     │
  └───────────────┬────────────────┘
                  │
                  └── kolejna iteracja ──▶ (powrót do „rodzic x”)
```

Pętla przebiega następująco:

1. P3 generuje zbiór kandydatów $C \subset \Lambda^*$ poprzez krzyżowanie kierowane drzewem powiązań; dla każdego
   rodzica wybranego do wariacji, każdy podzbiór powiązań w bieżącym modelu zależności jest odwiedzany w losowej
   kolejności, zgodnie ze standardowym przemiataniem optymalnego mieszania, a dla każdego podzbioru $F$ z populacji
   losowany jest dawca, proponujący modyfikację ograniczoną do $F$ (patrz Rodowód rodziców, dawców i przodków, poniżej);
2. każda proponowana modyfikacja $x'$ jest oceniana przez predyktor zastępczy względem jej bezpośredniego
   poprzednika w przemiataniu, $\hat{f}_1(x')$, uzyskiwana za pomocą $\hat{\delta}_F$;
3. modyfikacja jest tymczasowo akceptowana, jeśli $\hat{\delta}_F$ przewiduje nieujemną poprawę (domyślnie zerowy
   próg akceptacji; sekcja Wyniki ocenia wrażliwość na ten próg łącznie z $\kappa$), a przemiatanie jest kontynuowane
   od otrzymanego osobnika; w przeciwnym razie modyfikacja jest odrzucana, osobnik pozostaje niezmieniony, a
   przemiatanie przechodzi do następnego podzbioru powiązań w kolejności ustalonej w kroku 1;
4. gdy przemiatanie każdego rodzica zakończy się w całości albo zostanie skrócone przez opisany poniżej limit
   głębokości łańcucha $\kappa$, spośród wszystkich wyników przemiatania wybierany jest obiecujący podzbiór
   $C^* \subseteq C$ jako kandydaci niezdominowani w przestrzeni celów $(\hat{f}_1, f_2)$ ($C^*$ jest zbiorem selekcji
   lokalnym dla danej iteracji, odrębnym od globalnego frontu $\mathcal{P}^*$ z sekcji Sformułowanie Problemu, który
   przeszukiwanie z czasem aproksymuje);
5. każdy $x \in C^*$ przechodzi pełną ewaluację, dającą prawdziwą wartość $f_1(x)$;
6. $\mathcal{H}_t$ jest aktualizowane, $\hat{\delta}_F$ jest ponownie trenowana, a drzewo powiązań jest przebudowywane
   wraz z napływem nowych danych, ewoluując razem z populacją; w obrębie pojedynczej iteracji to samo drzewo
   zbudowane na jej początku jest wykorzystywane w przemiataniu każdego rodzica w kroku 1 i nie jest przebudowywane
   ponownie aż do kolejnego przejścia przez krok 6.

**Rodowód rodziców, dawców i przodków.** Rodzice dla kroku 1, a także przodek $x_0$ z konstrukcji teleskopowej, są zawsze losowani spośród osobników, które ukończyły kroki 5–6, czyli elementów $\mathcal{H}_t$ o rzeczywiście znanej wartości $f_1$, nigdy spośród przejściowych osobników opartych wyłącznie na predyktorze zastępczym. Konstrukcja teleskopowa nigdy więc nie kończy się na estymacie predyktora zastępczego. *(TODO: dawca losowany w kroku 1 nie podlega jeszcze temu samemu, jawnie stwierdzonemu ograniczeniu; doprecyzować, czy dawcy, podobnie jak rodzice i przodek $x_0$, również muszą pochodzić z $\mathcal{H}_t$, czy mogą być również przejściowymi osobnikami ocenionymi wyłącznie przez predyktor zastępczy w obrębie tego samego przemiatania.)*

**Zakres wierności.** P3Net działa wyłącznie przy pełnej wierności $r_K$: aparat niższej wierności wprowadzony w sekcji Sformułowanie Problemu jest mechanizmem na poziomie podłoża, konkretyzowanym tam, gdzie ma to zastosowanie, w sekcji Wyniki, lecz nie jest wykorzystywany przez opisaną powyżej pętlę przeszukiwania. Trenowanie predyktora zastępczego również na obserwacjach o niższej wierności jest alternatywą projektową omówioną w Podsumowaniu.

**Obsługa ograniczenia poprawności.** Kandydaci naruszający ograniczenie $g(x) \leq 0$ są odrzucani przed oceną przez predyktor zastępczy (tj.\ przed krokiem 2 powyższej pętli).

**Deduplikacja.** Duplikaty już obecne w $\mathcal{H}_t$ pomijają ponowną ewaluację. Jest to stosowane identycznie do każdej porównywanej metody w ramach wspólnej infrastruktury ewaluacyjnej (Wyniki, Kontrole rzetelności), więc ta oszczędność nie jest specyficzna dla P3Net; to zabezpieczenie ma istotne praktyczne znaczenie wobec redundancji genotyp–fenotyp udokumentowanej w NSGA-Net (Wprowadzenie) \citep{lu2019nsganet}. Sam koszt obliczeniowy $f_2$ jest obliczany analitycznie, bez udziału predyktora zastępczego (Sformułowanie Problemu), więc selekcja kandydatów do pełnej ewaluacji opiera się na niezdominowaniu w przestrzeni $(\hat{f}_1, f_2)$.

**Głębokość łańcucha ($\kappa$).** Aby ograniczyć akumulację błędu predyktora zastępczego wzdłuż przemiatania, narzucona jest maksymalna głębokość łańcucha $\kappa$ tymczasowo zaakceptowanych modyfikacji opartych wyłącznie na predyktorze zastępczym: gdy tylko wzdłuż danego przemiatania od ostatniej pełnej ewaluacji zaakceptowano $\kappa$ modyfikacji, bieżący osobnik jest wymuszany do $C^*$ niezależnie od jego przewidywanego $\hat{f}_1$. $\kappa$ jest inicjalizowana wartością własnej granicy eLyMPuS, $2\lceil\log_2(n)\rceil$ kroków, jako domyślną wartością heurystyczną, nie jako wyprowadzeniem z gwarancji monotoniczności, na której ta granica się opiera i która tutaj nie obowiązuje. Tu $n$ jest wymiarem pełnego, rozszerzonego, zdyskretyzowanego genotypu $\Lambda_1 \times \cdots \times \Lambda_n \times \Theta$, odpowiadającym zakresowi samego drzewa powiązań, nie liczbie uwzględniającej wyłącznie architekturę z sekcji Sformułowanie Problemu. Jej wrażliwość, łącznie z wrażliwością progu akceptacji z kroku 3 (również domyślną wartością heurystyczną, ustaloną powyżej na zero), jest oceniana empirycznie, a nie ustalana z założenia (Wyniki).

**Uzasadnienie projektowe (zaadaptowane z eLyMPuS).** Z adaptacji mechanizmu eLyMPuS do tego ustawienia wynikają trzy dalsze decyzje projektowe:

- Generowanie kandydatów podąża za pełnym przemiataniem optymalnego mieszania opisanym w kroku 1, zamiast pojedynczej modyfikacji na kandydata, dzięki czemu P3Net pozostaje spójny z operatorem wariacji, na którym opierają się własne gwarancje skuteczności P3.
- Gwarancja eLyMPuS odtworzenia brakującej zależności w ciągu $2\lceil\log_2(n)\rceil$ kroków opiera się na założeniu monotoniczności leżącego u podstaw krajobrazu dopasowania, którego nie oczekuje się w przypadku dokładności sieci neuronowej; $\hat{\delta}_F$ jest zatem traktowana jako wyuczony estymator heurystyczny bez tej gwarancji, a jej wiarygodność jest zamiast tego oceniana empirycznie poprzez analizę jakości predyktora zastępczego zaraportowaną w sekcji Wyniki.
- Niezdominowanie w kroku 4 jest ograniczone do kandydatów wytworzonych w obrębie tej samej iteracji przeszukiwania, tj.\ wywodzących się od przodków ewaluowanych względem tego samego migawkowego stanu $\mathcal{H}_t$, tak aby porównywane estymaty $\hat{f}_1$ dzieliły wspólny punkt odniesienia, zamiast być łączone między iteracjami z potencjalnie dryfującym predyktorem zastępczym.

---

## Wyniki

Niniejsza sekcja raportuje w podanej kolejności: jakość predyktora zastępczego, zbieżność przy ustalonych
budżetach ewaluacji, porównania frontu Pareto i hiperwolumenu oraz zbiorczą tabelę dla ustalonego budżetu (mediana,
IQR, skorygowane wartości $p$, wielkości efektu). Najpierw szczegółowo opisano konfigurację eksperymentalną i
protokół.

### Konfiguracja eksperymentalna

Protokół nie może pozwalać na odczytanie P3Net jako „P3 plus filtrowanie Pareto”. Jawnie określa, jaką mechanikę
selekcji NSGA-II wnosi do metody odniesienia, co zastępuje P3 (operator wariacji i rozkład propozycji) oraz, niezależnie
od wyboru silnika przeszukiwania, jaki wariant predyktora zastępczego jest stosowany (świadomy struktury powiązań
$\hat{\delta}_F$ względem bezwzględnego regresora), tak aby zyski można było przypisać właściwemu komponentowi, a nie
je ze sobą mieszać.

**Benchmark i przestrzeń przeszukiwania.** P3Net celuje w ustawienie wspólnego przeszukiwania architektury i
hiperparametrów, a nie w przestrzeń obejmującą wyłącznie architekturę. Zamiast rozstrzygać kwestię Kategorii 1 kontra
Kategorii 2 poprzez wybór pojedynczego benchmarku, celowo raportujemy oba obok siebie. Głównym benchmarkiem jest
JAHS-Bench-201 \citep{bansal2022jahsbench}, benchmark oparty na predyktorze zastępczym nad wspólną przestrzenią
przeszukiwania o dziesięciu wymiarach (sześć kategorycznych krawędzi architektury plus cztery hiperparametry, w tym
ciągły współczynnik uczenia i zanik wag), czternastu po doliczeniu czterech dodatkowych wymiarów wierności
(zgodnie z własną figurą źródła „14-wymiarowa przestrzeń przeszukiwania i wierności”), w trzech zbiorach danych; odpytuje
on wyuczony predyktor zastępczy nad pełną, mieszaną kategoryczno-ciągłą przestrzenią przeszukiwania bez rzeczywistego
treningu, więc nie istnieje enumerowalny front oracle (zob.\ Metryki, poniżej). NAS-HPO-Bench-II
\citep{hirose2021nashpobenchii}, stała tablica przeglądowa nad kombinacjami architektury i hiperparametrów, jest
raportowany obok niego jako odpowiednik z Kategorii 1: w zakresie stablicowanym wyczerpująco (do 12 epok treningu;
sekcja Prace pokrewne potwierdza, że $r_K$ jest ustalone na tym poziomie, a nie na osobnej, 200-epokowej ekstrapolacji
surogatu benchmarku), enumerowalny jest dokładny front oracle, co umożliwia
zastosowanie Inverted Generational Distance plus (IGD+) specyficznie na tym benchmarku. Każdy wynik utrzymujący się na
obu benchmarkach jest raportowany jako główne odkrycie; wynik utrzymujący się tylko na jednym jest raportowany jako
specyficzny dla tego benchmarku i nie jest uogólniany.

**Metody odniesienia.** NSGANetV2 (NSGA-II z bezwzględnym regresorem jako predyktorem zastępczym) jako podstawowa
metoda odniesienia; NSGANetV2 rozszerzony do ustawienia wspólnego z nieograniczonym, rzeczywistoliczbowym kodowaniem
$\Theta$ jako dodatkowa metoda kontrolna izolująca efekt samej dyskretyzacji, a nie silnika przeszukiwania czy
predyktora zastępczego (Kontrole rzetelności);
NSGA-Net (NSGA-II bez predyktora zastępczego, każdy kandydat w pełni ewaluowany) jako ablacja izolująca sam silnik po
stronie NSGA-II, symetryczna do opisanej poniżej ablacji izolującej sam silnik po stronie P3; sam P3, bez żadnego
predyktora zastępczego, jako ablacja izolująca sam silnik po stronie P3; P3 z bezwzględnym regresorem jako predyktorem
zastępczym (w stylu NSGANetV2) jako ablacja izolująca wyłącznie predyktor zastępczy, oddzielająca wkład projektu
świadomego struktury powiązań od wkładu samego silnika P3; SH-EMOA (wielokryterialny algorytm ewolucyjny oparty na
SMS-EMOA) oraz Multi-Objective Bayesian Optimization Hyperband (MO-BOHB), metody odniesienia ustanowione właśnie dla
tego ustawienia wspólnego na tych samych dwóch benchmarkach \citep{guerreroviu2021bagofbaselines}, uwzględnione
dlatego, że w odróżnieniu od NSGANetV2 nigdy nie były importowane z ustawienia ograniczonego do samej architektury i
nie wymagają takiego rozszerzenia; przeszukiwanie losowe oraz estymator Parzena o strukturze
drzewiastej (Tree-structured Parzen Estimator, TPE) jako metody odniesienia służące jako test poprawności (sanity
baselines). Ta siatka rozdziela wkłady silnika i predyktora zastępczego na tyle, na ile pozwala na to konstrukcja
eksperymentu, a nie jako pełny ortogonalny plan czynnikowy: relatywny predyktor zastępczy $\hat{\delta}_F$ świadomy
struktury powiązań jest zdefiniowany wyłącznie przy danym drzewie powiązań, więc nie da się skonstruować komórki
NSGA-II-plus-relatywny-predyktor-zastępczy, a wszelką różnicę przypisywaną „predyktorowi zastępczemu” poprzez
porównanie samego P3 z P3Net należy odczytywać z uwzględnieniem tej asymetrii.

Bez predyktora zastępczego, sam P3 stosuje kanoniczną regułę akceptacji optymalnego mieszania: każda proponowana
modyfikacja w obrębie przemiatania jest bramkowana rzeczywistą ewaluacją $f_1$, dokładnie tak, jak wyglądałby krok 3
pętli P3Net (Proponowany Optymalizator), gdyby $\hat{\delta}_F$ zastąpić samym $f_1$, oraz tak, jak w krokach
wspinaczkowych (hill-climbing) i mieszania międzypoziomowego oryginalnego algorytmu P3 \citep{goldman2014parameterless}.
Przy budżetach ewaluacji $\{50,\, 100,\, 200\}$ stosowanych tutaj (Budżety, poniżej) oczekuje się, że wyczerpie to
większość lub cały budżet w ciągu niewielkiej liczby przemiatań: dla wspólnego genotypu z dziesiątkami podzbiorów
powiązań, samo pełne przemiatanie jednego rodzica może zbliżyć się do najmniejszego poziomu budżetu. Nie jest to wada
tej ablacji, lecz właśnie jej sens: jeśli sam P3 załamuje się przy tym budżecie, wynik ten bezpośrednio motywuje
połączenie P3 z tanim predyktorem zastępczym w pierwszej kolejności, co jest właśnie tym, co faktycznie porównuje
pytanie centralne (Wprowadzenie). Dla tej konkretnej ablacji raportujemy liczbę ukończonych w ramach budżetu pełnych
przemiatań, obok jej hiperwolumenu, tak aby słaby wynik był odczytywany jako głód budżetowy, a nie jako porażka samego
silnika przeszukiwania.

**Akumulacja błędu predyktora zastępczego ($\kappa$ i próg akceptacji).** Powyższe główne porównanie ustala $\kappa$
na jej domyślnej wartości, czyli własnej granicy eLyMPuS wynoszącej $2\lceil\log_2(n)\rceil$ kroków (Proponowany
Optymalizator), a regułę akceptacji z kroku 3 na jej domyślnym progu zerowym ($\hat{\delta}_F \geq 0$). Oba parametry
są przemiatane łącznie w analizie wrażliwości: $\kappa$ na niewielkiej siatce (np.\ $\{1,\, \lceil\log_2(n)\rceil,\,
2\lceil\log_2(n)\rceil,\, \infty\}$), a próg akceptacji na niewielkiej siatce marginesów (np.\ $\{0,\, \epsilon,\,
2\epsilon\}$ dla ustalonego $\epsilon > 0$), przy niezmienionym poza tym P3Net, raportując hiperwolumen przy ustalonym
budżecie oraz korelację rangową predyktora zastępczego w funkcji obu parametrów.

**Kontrole rzetelności.** Identyczne kodowanie genotypu, funkcja dekodująca $D$, obsługa poprawności, budżet pełnej
ewaluacji, polityka ziaren losowości, reguła zatrzymania oraz pamięć podręczna deduplikacji (Proponowany Optymalizator)
we wszystkich porównywanych metodach, tak aby pozorna wydajność żadnej z metod nie korzystała z infrastruktury
niedostępnej innym. W szczególności dyskretyzacja ciągłych współrzędnych hiperparametrów (Proponowany Optymalizator)
jest stosowana identycznie do każdej metody odniesienia: NSGA-II/NSGANetV2 przeszukują to samo zdyskretyzowane $\Theta$
co P3Net, zamiast nieograniczonego, rzeczywistoliczbowego kodowania, jakiego użyłoby rozszerzenie NSGA-II/NSGANetV2 do
ustawienia wspólnego, tak aby wszelki zysk był przypisywalny silnikowi
przeszukiwania i predyktorowi zastępczemu, a nie różnicy w rozdzielczości genotypu. Wyrównuje to rozdzielczość, lecz
niekoniecznie jest neutralne: dyskretyzacja usuwa rzeczywistoliczbowe krzyżowanie, jakiego takie rozszerzenie
używałoby na
$\Theta$, nie kosztując przy tym nic P3, ponieważ P3 i tak działa na genotypie kategorycznym. Ta asymetria jest
ograniczana empirycznie, a nie jedynie odnotowywana: NSGANetV2 w swoim natywnym kodowaniu ciągłym jest uwzględniony
jako dodatkowa metoda kontrolna (Metody odniesienia, powyżej), tak aby wszelką przewagę P3Net można było sprawdzić
konkretnie względem porównania ze zdyskretyzowanym NSGANetV2, zamiast opierać się wyłącznie na porównaniu
zdyskretyzowanym.

**Budżety, ziarna losowości, zatrzymanie.** Trzy poziomy budżetu pełnej ewaluacji, $\{50,\, 100,\, 200\}$ pełnych
ewaluacji, podwajane na każdym kroku, tak aby tendencje zbieżności odczytywać na naturalnej, geometrycznej skali.
Każdy poziom jest zakotwiczony w wartości rzeczywiście stosowanej w otaczającej literaturze, a nie wybrany
arbitralnie: poziom środkowy odpowiada własnemu sugerowanemu przez JAHS-Bench-201 protokołowi ewaluacji wynoszącemu w
przybliżeniu 100 pełnych ewaluacji, przy minimum 10 ziaren losowości \citep{bansal2022jahsbench}; poziom najwyższy
pozostaje na poziomie lub poniżej 350 pełnych ewaluacji, jakich sam NSGANetV2 używa, by osiągnąć swoje raportowane
wyniki \citep{lu2020nsganetv2}, tak że żaden poziom nie przekracza reżimu, w którym pierwotnie wykazano, że
podstawowa metoda odniesienia działa dobrze. Utrzymuje to również każdy poziom poniżej własnej konwencji
NAS-HPO-Bench-II wynoszącej 500 prób przy benchmarkowaniu algorytmów przeszukiwania \citep{hirose2021nashpobenchii}.
To celowy wybór, nie przeoczenie: pytanie centralne dotyczy budżetu *ograniczonego* (Wprowadzenie), więc
wszystkie trzy poziomy testują reżim ciaśniejszy niż domyślny dla obu benchmarków, jednakowo. $R = 10$ niezależnych
przebiegów na metodę, z ustaloną, opublikowaną listą ziaren losowości, odpowiadającą zalecanemu minimum
JAHS-Bench-201; identyczny schemat inicjalizacji we wszystkich metodach; reguła zatrzymania obejmująca budżet
ewaluacji oraz, gdy przestrzeń przeszukiwania jest na tyle mała, by przedwcześnie osiągnąć zbieżność, kryterium
załamania eksploracji analogiczne do tego, które Bartnik musiała dodać dla przestrzeni o skali NAS-Bench-201
\citep{bartnik2026evolutionary}.

**Metryki.** Hiperwolumen przy ustalonym budżecie oraz, wyłącznie jeśli przestrzeń przeszukiwania dopuszcza
enumerowalny front oracle, IGD+; w przeciwnym razie w jego miejsce stosowany jest hiperwolumen względem najlepszego
znanego frontu *(TODO: precyzyjnie zdefiniować ten front, np.\ jako unię wszystkich punktów ewaluowanych przez
którąkolwiek porównywaną metodę we wszystkich przebiegach)*. Jakość predyktora zastępczego jest raportowana osobno jako korelacja rangowa (lub dokładność porównań
parowych, jeśli predyktor zastępczy jest relacyjny) między wartościami przewidywanymi a prawdziwymi w funkcji
$|\mathcal{H}_t|$.

**Plan statystyczny.** Zbiór porównań to P3Net przeciwstawiony każdemu z pozostałych dziewięciu wariantów (Metody
odniesienia, powyżej), w podziale na benchmark i poziom budżetu, nie każda parowa kombinacja spośród wszystkich
wariantów. Dla każdego porównania w tym zbiorze przeprowadzane są parowe testy rang znakowanych Wilcoxona, z
zastosowaną w ich obrębie korekcją Holma-Bonferroniego, a obok każdej skorygowanej wartości $p$ raportowana jest
wielkość efektu (np.\ delta Cliffa). Jest to podejście ściślejsze niż nieskorygowane porównania w najbliższej
wcześniejszej pracy \cite{bartnik2026evolutionary}, która nie raportuje wielkości efektu, a różnicę tę traktujemy jako
celowe udoskonalenie metodologiczne, a nie przeoczenie wymagające uzgodnienia.

**Diagnostyka.** Wskaźnik duplikacji genotypów oraz rotacja archiwum w trakcie przeszukiwania, motywowane
bezpośrednio redundancją na drodze od genotypu do fenotypu udokumentowaną w NSGA-Net (Wprowadzenie)
\cite{lu2019nsganet}, mierzone przy identycznym wspólnym kodowaniu genotypu ustalonym dla każdej porównywanej metody
(Kontrole rzetelności), tak aby wszelka różnica we wskaźniku duplikacji odzwierciedlała operator przeszukiwania, a
nie różnicę w kodowaniu. Pamięć podręczna deduplikacji (Proponowany Optymalizator) jest stosowana identycznie do
każdej porównywanej metody w ramach wspólnej infrastruktury ewaluacyjnej (Kontrole rzetelności), więc zmierzony
wskaźnik duplikacji odzwierciedla to, co proponuje każdy operator przeszukiwania, a nie artefakt asymetrycznego
cache'owania. Wskaźnik ten liczymy w chwili propozycji, dla każdego kandydata wygenerowanego przez operator
przeszukiwania, niezależnie od tego, czy zostanie później przechwycony przez pamięć podręczną, nie w chwili
ewaluacji; dzięki temu pozostaje informatywny, mimo że sama pamięć podręczna tłumi ponowną ewaluację wszystkiego, co
liczy. Krzywe zbieżności, postęp frontu Pareto, stabilność między ziarnami losowości.

**Odtwarzalność.** Każda zapisana w pamięci podręcznej ewaluacja jest indeksowana genotypem, typem eksperymentu oraz
ciągiem znaków wersji protokołu obejmującym każde ustawienie wpływające na zarejestrowaną wartość, tak aby zmiana
któregokolwiek z nich automatycznie unieważniała nieaktualne wpisy w pamięci podręcznej, zgodnie ze wzorcem
zastosowanym przez \cite{bartnik2026evolutionary}.

---

## Podsumowanie

- P3Net łączy dwie komplementarne idee: P3 buduje model strukturalnych zależności w genotypie, a predyktor zastępczy eliminuje kosztowne ewaluacje nieobiecujących kandydatów.
- Odpowiedź na pytanie badawcze: czy modelowanie zależności przez P3 przekłada się na lepszą efektywność pętli wspomaganej predyktorem zastępczym w porównaniu z NSGANetV2.
- Ograniczenia: jakość predyktora zastępczego zależy od jakości kodowania genotypu; drzewo powiązań budowane jest na podstawie informacji wzajemnej między parami zmiennych, co może być zbyt grubym sygnałem, by uchwycić wyższego rzędu, głęboko ustrukturyzowane zależności.
- Przyszłe kierunki: silniejszy model predyktora zastępczego (GNN nad grafem komórki), uczenie aktywne do decydowania, których kandydatów poddać pełnej ewaluacji, rozszerzenie na przestrzenie architektur o zmiennej głębokości; trenowanie predyktora zastępczego również na obserwacjach o niższej wierności $f_1^{(k)}$, $k<K$, zamiast wyłącznie na pełnych ewaluacjach przy $r_K$ jak w niniejszej pracy, z wykorzystaniem drabiny wierności już wprowadzonej w sekcji Sformułowanie Problemu. Pominęliśmy to tutaj, by utrzymać redukcję kosztu pętli przeszukiwania jako czysto przypisywalną samemu relatywnemu predyktorowi zastępczemu; to naturalna kolejna dźwignia, gdy ta przypisywalność zostanie już ustalona.

---

## Bibliografia

1. G. Andreadis, T. Alderliesten, P. A. N. Bosman, "Fitness-based Linkage Learning and Maximum-Clique Conditional Linkage Modelling for Gray-Box Optimization with RV-GOMEA," w: *Proceedings of the Genetic and Evolutionary Computation Conference (GECCO)*, 2024.
2. A. Bansal, D. Stoll, M. Janowski, A. Zela, F. Hutter, "JAHS-Bench-201: A Foundation For Research On Joint Architecture And Hyperparameter Search," w: *Advances in Neural Information Processing Systems 35 (NeurIPS 2022), Datasets and Benchmarks Track*, 2022.
3. N. Bartnik, *Evolutionary optimization of deep neural networks*, praca magisterska, Politechnika Wrocławska, Wydział Elektroniki, Fotoniki i Mikrosystemów, promotor: Michał Przewoźniczek, 2026.
4. A. Bouter, P. A. N. Bosman, "A Joint Python/C++ Library for Efficient yet Accessible Black-Box and Gray-Box Optimization with GOMEA," w: *Companion Proceedings of the Genetic and Evolutionary Computation Conference (GECCO Companion)*, 2023.
5. X. Dong, Y. Yang, "NAS-Bench-201: Extending the Scope of Reproducible Neural Architecture Search," w: *International Conference on Learning Representations (ICLR)*, 2020.
6. A. Dushatskiy, A. M. Mendrik, T. Alderliesten, P. A. N. Bosman, "Convolutional neural network surrogate-assisted GOMEA," w: *Proceedings of the Genetic and Evolutionary Computation Conference (GECCO)*, 2019, s. 753–761.
7. A. Dushatskiy, T. Alderliesten, P. A. N. Bosman, "A Novel Surrogate-assisted Evolutionary Algorithm Applied to Partition-based Ensemble Learning," w: *Proceedings of the Genetic and Evolutionary Computation Conference (GECCO '21)*, 2021.
8. B. W. Goldman, W. F. Punch, "Parameter-less population pyramid," w: *Proceedings of the 2014 Annual Conference on Genetic and Evolutionary Computation (GECCO)*, 2014, s. 785–792.
9. J. Guerrero-Viu, S. Hauns, S. Izquierdo, G. Miotto, S. Schrodi, A. Biedenkapp, T. Elsken, D. Deng, M. Lindauer, F. Hutter, "Bag of Baselines for Multi-objective Joint Neural Architecture Search and Hyperparameter Optimization," arXiv:2105.01015, 2021.
10. Y. Hirose, N. Yoshinari, S. Shirakawa, "NAS-HPO-Bench-II: A Benchmark Dataset on Joint Optimization of Convolutional Neural Network Architecture and Training Hyperparameters," w: *Proceedings of the Asian Conference on Machine Learning (ACML)*, 2021.
11. Y. Liu, Y. Sun, B. Xue, M. Zhang, G. G. Yen, K. C. Tan, "A survey on evolutionary neural architecture search," *IEEE Transactions on Neural Networks and Learning Systems*, t. 34, nr 2, s. 550–570, 2023.
12. Z. Lu, I. Whalen, V. Boddeti, Y. Dhebar, K. Deb, E. Goodman, W. Banzhaf, "NSGA-Net: neural architecture search using multi-objective genetic algorithm," w: *Proceedings of the Genetic and Evolutionary Computation Conference (GECCO)*, 2019, s. 419–427.
13. Z. Lu, K. Deb, E. Goodman, W. Banzhaf, V. N. Boddeti, "NSGANetV2: Evolutionary Multi-Objective Surrogate-Assisted Neural Architecture Search," w: *Proceedings of the European Conference on Computer Vision (ECCV)*, 2020.
14. Z. Lu, R. Cheng, S. Huang, H. Zhang, C. Qiu, F. Yang, "Surrogate-assisted Multi-objective Neural Architecture Search for Real-time Semantic Segmentation," arXiv:2208.06820, 2022.
15. F. N. Özçelik, M. Ö. Efe, "Evolutionary neural architecture search: a survey," *Turkish Journal of Electrical Engineering and Computer Sciences*, t. 34, nr 4, s. 507–541, 2026.
16. M. W. Przewoźniczek, F. Chicano, M. M. Komarnicki, R. Tinós, "Limited Perfect Monotonical Surrogates Constructed Using Low-Cost Recursive Linkage Discovery with Guaranteed Output," w: *Proceedings of the Genetic and Evolutionary Computation Conference (GECCO)*, 2026, s. 645–653.
17. D. Thierens, P. A. N. Bosman, "Optimal Mixing Evolutionary Algorithms," w: *Proceedings of the 13th Annual Conference on Genetic and Evolutionary Computation (GECCO)*, 2011, s. 617–624.
18. K. H. Tran, L. Truong, A. Vo, N. H. Luong, "Accelerating Gene-pool Optimal Mixing Evolutionary Algorithm for Neural Architecture Search with Synaptic Flow," w: *Companion Proceedings of the Genetic and Evolutionary Computation Conference (GECCO Companion)*, 2023, s. 85–86.
19. C. White, M. Safari, R. Sukthanker, B. Ru, T. Elsken, A. Zela, D. Dey, F. Hutter, "Neural Architecture Search: Insights from 1000 Papers," arXiv:2301.08727, 2023.
20. L. D. Whitley, F. Chicano, B. W. Goldman, "Gray Box Optimization for Mk Landscapes (NK Landscapes and MAX-kSAT)," *Evolutionary Computation*, t. 24, nr 3, s. 491–519, 2016.
21. C. Ying, A. Klein, E. Christiansen, E. Real, K. Murphy, F. Hutter, "NAS-Bench-101: Towards Reproducible Neural Architecture Search," w: *Proceedings of the 36th International Conference on Machine Learning (ICML)*, 2019, s. 7105–7114.
22. K. Yu, C. Sciuto, M. Jaggi, C. Musat, M. Salzmann, "Evaluating the Search Phase of Neural Architecture Search," w: *International Conference on Learning Representations (ICLR)*, 2020.
23. A. Zela, A. Klein, S. Falkner, F. Hutter, "Towards Automated Deep Learning: Efficient Joint Neural Architecture and Hyperparameter Search," w: *ICML 2018 AutoML Workshop*, 2018.

---

## Notatki: Dziennik decyzji dotyczących sformułowania problemu

*Dziennik roboczy, niebędący częścią recenzowanej treści manuskryptu: każda decyzja architektoniczna podjęta przy formułowaniu problemu, predyktora zastępczego i silnika przeszukiwania, wraz z uzasadnieniem każdego wyboru oraz miejscem, w którym żyje w tekście powyżej.*

### Reprezentacja problemu

| Decyzja | Co dokładnie | Uzasadnienie / konsekwencja | Gdzie |
|---|---|---|---|
| Genotyp architektury | Wektor $x=(x_1,\dots,x_n)\in\Lambda$, każde $x_i$ z skończonego zbioru operacji na krawędzi grafu komórki | Standardowe kodowanie cell-based NAS (jak w NSGA-Net) | Sformułowanie Problemu |
| Rozszerzenie na wspólne przeszukiwanie | $\Lambda \to \Lambda_1\times\cdots\times\Lambda_n\times\Theta$, $\Theta\subset\mathbb{R}^m$ dla hiperparametrów treningowych (LR, weight decay) | Odpowiedź na Zela i in.: architektura i hiperparametry współzależą się, więc sekwencyjne strojenie jest zawodne | Sformułowanie Problemu |
| Zakres $\Theta$ | Tylko procedura treningowa (LR, weight decay); pojemność strukturalna (liczba komórek, szerokość kanałów) zostaje częścią architektury / osi wierności, nie $\Theta$ | Zgodne z konwencją całej literatury joint NAS+HPO (JAHS-Bench-201, NAS-HPO-Bench-II, Zela i in.) | Prace pokrewne |
| Obsługa ciągłości $\Theta$ w P3 | **Dyskretyzacja** (opcja i): każda współrzędna $\Theta$ binowana na skończony zbiór przed uczeniem linkage; brak osobnego mechanizmu mixingu | Świadomy kompromis: mniejsza rozdzielczość HP-space za czystość central question (nie miesza testu P3 z testem nowego mechanizmu continuous-mixing); RV-GOMEA-style zostawione jako future work | Proponowany Optymalizator |
| Kodowanie w baselinach | Ta sama dyskretyzacja $\Theta$ narzucona też na NSGA-II/NSGANetV2 (odchodzą od swojego standardowego real-valued crossoveru); dodatkowo NSGANetV2 uruchomiony osobno w swoim natywnym, ciągłym kodowaniu jako kontrola | Dyskretyzacja jest wymogiem „identycznego kodowania genotypu” dla fairness, ale nie jest neutralna: kosztuje NSGA-II/NSGANetV2 ich natywny crossover, podczas gdy P3 nic to nie kosztuje; run kontrolny w kodowaniu ciągłym ogranicza tę asymetrię empirycznie zamiast tylko zakładać fairness z definicji | Wyniki, Kontrole rzetelności |

### Dekodowanie i poprawność

| Decyzja | Co dokładnie | Uzasadnienie / konsekwencja | Gdzie |
|---|---|---|---|
| Dekodowanie | $D:\Lambda\to\mathcal{N}$, mapuje genotyp na sieć | — | Sformułowanie Problemu |
| Walidacja | Ograniczenie $g(x)\le 0$ (np. brak ścieżki input–output); $\Lambda^*$ = zbiór poprawnych genotypów | Nie każdy genotyp dekoduje się do działającej sieci | Sformułowanie Problemu |
| Odrzucanie nieprawidłowych kandydatów | $g(x)>0$ odrzucane przed oceną surogatu | Oszczędność kosztu obliczeniowego surogatu | Proponowany Optymalizator |

### Co optymalizujemy

| Decyzja | Co dokładnie | Uzasadnienie / konsekwencja | Gdzie |
|---|---|---|---|
| Cel 1 | $f_1(x)$ = błąd walidacji sieci $D(x)$, minimalizowany | Standardowa jakość predykcyjna | Sformułowanie Problemu |
| Cel 2 | $f_2(x)=\phi(D(x))$ = koszt obliczeniowy (parametry lub FLOPs), liczony analitycznie, minimalizowany | Klasyczna dwukryterialna formuła NAS (jakość vs. koszt) | Sformułowanie Problemu |
| Rozdzielczość dla $f_2$ | Ustalona na wartości najwyższego poziomu wierności $r_K$, niezależnie od poziomu, na którym akurat pytany jest $f_1$ | $f_2$ nie może „pływać” z poziomem wierności — zapewnia porównywalność kosztu między kandydatami | Sformułowanie Problemu |
| Formuła wielokryterialna | Front Pareto $\mathcal{P}^*$ — standardowa relacja dominacji nad $(f_1,f_2)$ | — | Sformułowanie Problemu |

### Budżet i wierność oceny

| Decyzja | Co dokładnie | Uzasadnienie / konsekwencja | Gdzie |
|---|---|---|---|
| Drabina wierności | $r_1<\dots<r_K$, uporządkowana po liczbie epok; jeśli benchmark ma dodatkowe osie zasobów (np. rozdzielczość), każdy poziom ustala też ich wartość | Zdefiniowana jako ogólny mechanizm na poziomie substratu (nieprzypisany do konkretnego benchmarku); pełna ewaluacja $f_1$ jest droga, więc drabina to naturalny wehikuł do taniego filtrowania przy niższej wierności, *jeśli* dana metoda z niego korzysta | Sformułowanie Problemu |
| Zakres wierności własnego P3Net | P3Net działa wyłącznie na pełnej wierności $r_K$; drabina **nie** jest wykorzystywana przez pętlę przeszukiwania — żaden kandydat nie jest oceniany przez $f_1^{(k)}$, $k<K$; żaden z baseline'ów w Wynikach też z niej nie korzysta | Utrzymuje czystą atrybucję redukcji kosztu wyłącznie do surogatu relatywnego, bez trzeciej, nieablowanej dźwigni kosztowej; utrzymana jako ogólna infrastruktura na wypadek przyszłego baseline'u multi-fidelity (np. opartego na Hyperbandzie), nie jako aktywny element obecnego porównania; trenowanie na niższych wiernościach odnotowane jako future work | Proponowany Optymalizator; Wyniki; Podsumowanie |
| Obsługa szumu | Substraty stochastyczne (trening na żywo, powtórzenia z benchmarku): $s$ ziaren losowych, mediana do selekcji i raportowania; substraty deterministyczne (surogat benchmarku): bez uśredniania. Oba wybrane benchmarki P3Net są deterministyczne, więc $s=1$ w całej pracy | Rzetelność selekcji przy niedeterministycznej ocenie, utrzymana ogólnie na przyszłość dla substratów stochastycznych; $s$ (powtórzenia jednego zapytania) to co innego niż $R$ (niezależne przebiegi przeszukiwania, Wyniki) — oba pojęcia nie powinny być mylone | Sformułowanie Problemu |
| Rozliczanie kosztu | Wyłącznie w wywołaniach $f_1$ (pełnych ewaluacjach), nigdy w wywołaniach $\hat{\delta}_F$ | Zgodne z motywacją całej pracy — koszt pełnej ewaluacji to wąskie gardło | Sformułowanie Problemu |

### Silnik przeszukiwania

| Decyzja | Co dokładnie | Uzasadnienie / konsekwencja | Gdzie |
|---|---|---|---|
| Algorytm | P3 zamiast NSGA-II | Testowana hipoteza: świadomość struktury zależności > crowding distance przy tym samym budżecie | Proponowany Optymalizator |
| Struktura piramidy | P3 zamiast jednej populacji o stałym rozmiarze rozwija uporządkowaną piramidę populacji o rosnącym rozmiarze, dodając nowy poziom dopiero gdy istniejące poziomy przestają przynosić poprawę — własność „parameter-less” | Wyjaśnia, skąd nazwa „piramida”; kanonicznie, awans jednego rozwiązania w górę piramidy kosztuje prawdziwą ewaluację za każdą zaakceptowaną lokalną poprawę, dlatego ablacja P3 bez surogatu jest przewidywalnie głodzona budżetowo (patrz wiersz Metody odniesienia niżej) | Prace pokrewne |
| Drzewo linkage | Aglomeracyjny UPGMA nad znormalizowaną informacją wzajemną między zmiennymi genotypu, standardowa procedura P3, bez modyfikacji dla części architektonicznej | Powtórne użycie sprawdzonego mechanizmu P3 bez zmian | Proponowany Optymalizator |
| Granulacja przebudowy drzewa | Stałe dla wszystkich sweepów w obrębie jednej iteracji; przebudowywane tylko w kroku 6, na granicy iteracji | Usuwa niejasność, czy drzewo mogłoby się zmienić w trakcie sweepu — nie może | Proponowany Optymalizator |
| Crossover | Na poziomie grup zmiennych (linkage subsets), nie pojedynczych genów | Chroni wykryte grupy powiązanych decyzji projektowych przed rozerwaniem | Proponowany Optymalizator |

### Surogat

| Decyzja | Co dokładnie | Uzasadnienie / konsekwencja | Gdzie |
|---|---|---|---|
| Typ surogatu | **Względny i linkage-aware**: $\hat{\delta}_F(x,x')\approx f_1(x)-f_1(x')$ dla pary różniącej się tylko na podzbiorze $F$, zamiast regresji bezwzględnej z pełnego kodowania (jak NSGANetV2) | To jest właściwy punkt różnicujący P3Net od NSGANetV2 już na poziomie sformułowania problemu | Sformułowanie Problemu |
| Rodowód mechanizmu | Mechanicznie bliżej CS-GOMEA (regresja ciągłej różnicy fitness, brak gwarancji formalnej); filozoficznie bliżej eLyMPuS, empirycznego wariantu LyMPuS (relatywność, struktura powiązań odkrywana przyrostowo, niezakładana z góry) | NAS validation accuracy nie dekomponuje się na podfunkcje (brak dostępu gray-box) — oba mechanizmy są dopasowane do tego reżimu czarnej skrzynki, ale różnią się na dwóch niezależnych osiach (mechanizm obliczeniowy, gwarancja formalna) | Prace pokrewne |
| Rekonstrukcja wartości bezwzględnej | Telescoping wzdłuż łańcucha zaakceptowanych modyfikacji do najbliższego w pełni ocenionego przodka: $\hat f_1(x_m)=f_1(x_0)-\sum_i\hat\delta_{F_i}$ | Pozwala ocenić kandydata z głębi sweepu bez pełnej ewaluacji na każdym kroku | Proponowany Optymalizator |
| Gwarancja przodka | $x_0$ zawsze pochodzi z $\mathcal{H}_t$ (ukończone kroki 5–6), nigdy z osobnika ocenionego wyłącznie przez surogat w trakcie sweepu | Zamyka lukę, w której konstrukcja telescoping mogłaby się oprzeć na nieznanym $f_1(x_0)$ | Proponowany Optymalizator |
| Trening surogatu | Na różnicach parami z $\mathcal{H}_t$ (zbiór dotychczasowych pełnych ewaluacji) | — | Sformułowanie Problemu |
| Odświeżanie | $\mathcal{H}_t$, $\hat\delta_F$ i drzewo linkage przebudowywane po każdej rundzie pełnych ewaluacji | Surogat i struktura zależności ewoluują razem z populacją | Proponowany Optymalizator |

### Pętla przeszukiwania

| Krok | Co się dzieje | Gdzie |
|---|---|---|
| 1 | P3 generuje kandydatów przez pełny sweep optimal mixing wzdłuż drzewa linkage | Proponowany Optymalizator |
| 2 | Każda propozycja oceniana względnie przez $\hat\delta_F$ względem bezpośredniego poprzednika w sweepie | Proponowany Optymalizator |
| 3 | Akceptacja tymczasowa, jeśli surogat przewiduje nieujemną poprawę (domyślny próg zero, testowany w Wynikach); inaczej odrzucenie i przejście do następnego podzbioru | Proponowany Optymalizator |
| 4 | Po zakończeniu sweepu (lub odcięciu przez $\kappa$) wybór $C^*$ = kandydaci niezdominowani w $(\hat f_1, f_2)$ | Proponowany Optymalizator |
| 5 | Pełna ewaluacja każdego $x\in C^*$ | Proponowany Optymalizator |
| 6 | Aktualizacja $\mathcal{H}_t$, retrening $\hat\delta_F$, przebudowa drzewa linkage | Proponowany Optymalizator |

### Zabezpieczenia i parametry pomocnicze

| Decyzja | Co dokładnie | Uzasadnienie / konsekwencja | Gdzie |
|---|---|---|---|
| Deduplikacja | Kandydaci już obecni w $\mathcal{H}_t$ pomijają ponowną ewaluację; stosowana identycznie dla każdej porównywanej metody jako część wspólnej infrastruktury ewaluacji, nie tylko w pętli P3Net | Bezpośrednia odpowiedź na redundancję genotyp→fenotyp z NSGA-Net; jednolite stosowanie zapobiega temu, by ta oszczędność sztucznie zawyżała efektywność P3Net względem baseline'ów, które równie dobrze mogłyby z niej korzystać | Proponowany Optymalizator; Wyniki, Kontrole rzetelności |
| Głębokość łańcucha $\kappa$ | Maksymalna liczba tymczasowo zaakceptowanych modyfikacji zanim wymuszona zostanie pełna ewaluacja | Ogranicza akumulację błędu surogatu wzdłuż sweepu | Proponowany Optymalizator |
| Próg akceptacji | Reguła akceptacji w kroku 3 używa domyślnie progu zero ($\hat\delta_F \geq 0$) | Najprostsza heurystyka zgodna ze standardową akceptacją optimal mixing (brak pogorszenia); testowana łącznie z $\kappa$, a nie zakładana za wystarczającą | Proponowany Optymalizator; Wyniki |
| Wartość domyślna $\kappa$ | Inicjalizowana granicą $2\lceil\log_2 n\rceil$ z eLyMPuS, gdzie $n$ to wymiar pełnego, rozszerzonego, zdyskretyzowanego genotypu (architektura + $\Theta$), nie liczba z sekcji Sformułowanie Problemu dotycząca tylko architektury — jako heurystyka, *nie* jako wyprowadzenie z gwarancji monotoniczności (która tu nie obowiązuje) | Uczciwe przyznanie, że gwarancja teoretyczna nie przenosi się na NAS; wrażliwość testowana empirycznie, łącznie z progiem akceptacji powyżej | Proponowany Optymalizator; Wyniki |
| Pełny sweep, nie pojedyncza modyfikacja | Generowanie kandydatów zawsze przez cały optimal mixing sweep | Spójność z operatorem wariacji, na którym opierają się gwarancje P3 | Proponowany Optymalizator |
| Brak gwarancji dla $\hat\delta_F$ | Traktowany jako heurystyczny estymator uczony, bez gwarancji eLyMPuS (złamane założenie monotoniczności fitness) | Ostrożność naukowa — nie przenosi teoretycznej gwarancji do domeny, gdzie nie obowiązuje | Proponowany Optymalizator |
| Spójność referencji przy nondominacji | Porównanie niezdominowania w kroku 4 tylko w obrębie tej samej iteracji (ten sam snapshot $\mathcal{H}_t$) | Zapobiega mieszaniu estymat $\hat f_1$ z dryfującym surogatem między iteracjami | Proponowany Optymalizator |

### Benchmarki i zakres eksperymentalny

| Decyzja | Co dokładnie | Uzasadnienie / konsekwencja | Gdzie |
|---|---|---|---|
| Benchmarki podstawowe | JAHS-Bench-201 (Kategoria 2 — surogat ciągły, brak enumerowalnego oracle) i NAS-HPO-Bench-II (Kategoria 1 — dyskretna siatka, dokładny oracle) — oba, celowo, obok siebie | Deterministyczny cel, policzalny front oracle, ograniczony budżet; wynik trzymający się na obu jest raportowany jako główny, na jednym — jako specyficzny | Prace pokrewne; Wyniki |
| Metody odniesienia | NSGANetV2 (główny, zdyskretyzowane $\Theta$); NSGANetV2 w natywnym, ciągłym $\Theta$ (kontrola izolująca efekt samej dyskretyzacji); NSGA-Net bez surogatu, każdy kandydat w pełni ewaluowany (ablacja silnika, strona NSGA-II, symetryczna do wiersza P3 poniżej); P3 bez surogatu (ablacja silnika, strona P3); P3 + regresor bezwzględny w stylu NSGANetV2 (ablacja surogatu); SH-EMOA i MO-BOHB, metody odniesienia ustanowione właśnie dla tego ustawienia wspólnego na tych samych dwóch benchmarkach [guerreroviu2021bagofbaselines]; przeszukiwanie losowe i TPE (test poprawności) | Przypisuje zysk do silnika vs. surogatu vs. dyskretyzacji na tyle, na ile pozwala projekt; nie jest to pełna ortogonalna faktoryzacja, bo surogat relatywny $\hat\delta_F$ jest zdefiniowany tylko przy istniejącym drzewie linkage, więc komórka NSGA-II + surogat relatywny nie istnieje. SH-EMOA/MO-BOHB dodane, bo w odróżnieniu od NSGANetV2 nigdy nie były importowane z ustawienia ograniczonego do samej architektury i nie wymagają takiego rozszerzenia | Wyniki |
| Rzeczywistość budżetowa P3-bez-surogatu | Stosuje kanoniczną regułę akceptacji optimal mixing: każdy zaakceptowany krok w sweepie jest bramkowany przez *prawdziwą* ewaluację $f_1$, jak we własnym hill-climbingu/mixowaniu międzypoziomowym P3 | Oczekiwane wyczerpanie większości lub całości budżetu 50–200 w bardzo niewielu sweepach; raportowane wprost (liczba pełnych sweepów ukończonych w budżecie), by słaby wynik czytał się jako głód budżetowy, nie porażka silnika — ten kolaps sam w sobie jest informacyjny, uzasadnia potrzebę surogatu | Wyniki, Metody odniesienia |
| Poziomy budżetu pełnych ewaluacji | Trzy poziomy, $\{50, 100, 200\}$ pełnych ewaluacji, podwajające się na każdym kroku; $R=10$ niezależnych ziaren losowych | Zweryfikowane względem trzech konkretnych liczb z literatury, nie dobrane arbitralnie: (1) własny sugerowany protokół JAHS-Bench-201 to ≈100 ewaluacji, min. 10 ziaren [bansal2022jahsbench] — odpowiada wprost poziomowi środkowemu i $R$; (2) sam NSGANetV2 używa dokładnie 350 pełnych ewaluacji (Tabela 2), by osiągnąć swoje raportowane wyniki [lu2020nsganetv2] — górny poziom (200) pozostaje poniżej tej wartości; (3) własny artykuł NAS-HPO-Bench-II benchmarkuje algorytmy przeszukiwania przy 500 próbach [hirose2021nashpobenchii] — wszystkie trzy poziomy pozostają poniżej i tej wartości, celowo, bo pytanie centralne dotyczy budżetu *ograniczonego* (Wprowadzenie) | Wyniki |
| Metryki | Hiperwolumen przy stałym budżecie zawsze; IGD+ tylko gdy front oracle jest enumerowalny (czyli tylko na NAS-HPO-Bench-II) | Metryka dopasowana do tego, co dany benchmark faktycznie oferuje | Wyniki |
| Plan statystyczny | Sparowany test Wilcoxona + korekcja Holma-Bonferroniego + wielkość efektu (np. delta Cliffa) przy każdej wartości $p$ | Świadomie surowsze niż niekorygowane porównania u Bartnik | Wyniki |
| Zbiór porównań do korekcji | P3Net vs. każde z pozostałych dziewięciu ramion, osobno per benchmark i poziom budżetu — nie każda możliwa para wśród wszystkich ramion | Precyzuje, po czym dokładnie liczy się korekcja Holma-Bonferroniego, bo skorygowany próg istotności zależy od tej liczby | Wyniki, Plan statystyczny |
| Diagnostyka | Wskaźnik duplikacji genotypów i rotacja archiwum, mierzone pod identycznym kodowaniem genotypu *oraz* identycznie stosowanym cache'em deduplikacji dla wszystkich metod; liczone w momencie propozycji, nie ewaluacji | Sprawdza empirycznie, czy motywacja z NSGA-Net (redundancja duplikatów) faktycznie przenosi się na wspólny genotyp arch+HP — jabłka do jabłek między metodami, bez zaburzenia przez asymetryczne cache'owanie ani przez punkt pomiaru | Wyniki |
| Reprodukowalność | Cache kluczowany genotypem, typem eksperymentu i wersją protokołu | Automatyczna inwalidacja cache przy zmianie ustawień | Wyniki |

### Granice zakresu (co świadomie wyłączone / odróżnione)

| Decyzja | Co dokładnie | Gdzie |
|---|---|---|
| Gray-box vs. black-box | P3Net działa w czarnej skrzynce (dokładność NAS niedekomponowalna); explicite odróżnione od optymalizacji gray-box Whitleya/Chicano/Goldmana używanej w linii GOMEA | Prace pokrewne |
| Surogat benchmarku vs. surogat search-time | Surogat JAHS-Bench-201 zastępuje cel raz, offline, przed przeszukiwaniem; surogat P3Net dopasowywany przyrostowo podczas przeszukiwania — dwie niezależne decyzje projektowe | Prace pokrewne |
| Delta względem najbliższej pracy (Bartnik) | Bartnik: regresor bezwzględny, metody odniesienia MO-LS/MO-P3-GOMEA (nie NSGA-II/NSGANetV2), tylko architektura (NAS-Bench-201, brak $\Theta$) — P3Net różni się na wszystkich trzech osiach naraz | Prace pokrewne |

### Ustalone decyzje recenzyjne (nie otwierać ponownie bez nowej informacji)

*Przed zgłoszeniem problemu w nowym przebiegu recenzji sprawdź najpierw tę tabelę. Pozycje „Naprawione” zostały już zaadresowane w tekście pod wskazaną lokalizacją. Pozycje „Odrzucone” zostały rozważone i świadomie pozostawione bez zmian — ponowne zgłaszanie ich jako nieodkrytych nie jest użyteczne bez konkretnego powodu, dla którego odrzucenie przestało obowiązywać. Ta tabela sama w sobie nie podlega ocenie, zgodnie ze standardową instrukcją dla recenzenta.*

| Punkt | Status | Rozwiązanie / powód | Gdzie |
|---|---|---|---|
| Prace pokrewne po Proponowanym Optymalizatorze | Odrzucone | Świadoma decyzja autora, potwierdzona po recenzji; odwołania w przód (eLyMPuS, linia GOMEA) rozwiązane przez krótki gloss przy pierwszym użyciu zamiast zmiany kolejności sekcji | Wprowadzenie; Proponowany Optymalizator |
| Zakres cache'a deduplikacji | Naprawione | Stosowany identycznie do każdej porównywanej metody jako wspólna infrastruktura, nie tylko w P3Net | Proponowany Optymalizator; Wyniki |
| Asymetria dyskretyzacji (NSGA-II traci natywny crossover, P3 nie) | Naprawione | Ograniczona empirycznie przez kontrolny baseline NSGANetV2 w natywnym, ciągłym $\Theta$, nie tylko przyznana wprost | Wyniki, Metody odniesienia/Kontrole rzetelności |
| Ablacja silnik×surogat nie jest pełną faktoryzacją | Naprawione | Stwierdzone wprost: surogat relatywny wymaga drzewa linkage, więc komórka NSGA-II+surogat relatywny nie istnieje | Wyniki, Metody odniesienia |
| Kolizja notacyjna $\mathcal{H}_t$ vs. $D$ | Naprawione | Zbiór obserwacji przemianowany na $\mathcal{H}_t$ wszędzie | Sformułowanie Problemu; Proponowany Optymalizator; Wyniki |
| Drabina wielo-wierności: aparat vs. nieużywana w praktyce | Naprawione | Stwierdzone wprost, że żaden obecny baseline z niej nie korzysta; utrzymana jako ogólna infrastruktura na przyszły baseline multi-fidelity | Sformułowanie Problemu |
| Poziomy budżetu pełnych ewaluacji bez źródła | Naprawione | $\{50,100,200\}$, $R=10$, każdy zakotwiczony w zweryfikowanej liczbie z literatury (protokół JAHS-Bench-201, 350 z NSGANetV2, 500 z NAS-HPO-Bench-II) | Wyniki, Budżety |
| Ablacja „P3 bez surogatu”: niezdefiniowany mechanizm akceptacji i wykonalność budżetowa | Naprawione | Kanoniczna reguła akceptacji optimal mixing (prawdziwe $f_1$ bramkuje każdy zaakceptowany krok) stwierdzona wprost; oczekiwany głód budżetowy podany jako wynik informacyjny, nie ukryty; liczba ukończonych sweepów w budżecie raportowana jako diagnostyka | Wyniki, Metody odniesienia |
| Brak baseline'u engine-only po stronie NSGA-II (asymetria z „P3 bez surogatu”) | Naprawione | Dodano: NSGA-Net (bez surogatu, pełny trening każdego kandydata) jako symetryczna ablacja silnika | Wyniki, Metody odniesienia |
| Kolizja terminologiczna $s$ (ziarna szumu ewaluacji) vs. $R$ (niezależne przebiegi) | Naprawione | Rozróżnione wprost; oba wybrane benchmarki są deterministyczne, więc $s=1$ w całej pracy | Sformułowanie Problemu |
| Domyślna granica $\kappa$: czy $n$ obejmuje $\Theta$? | Naprawione | Doprecyzowane: $n$ to wymiar pełnego, rozszerzonego, zdyskretyzowanego genotypu | Proponowany Optymalizator |
| Konstrukcja telescoping: czy przodek $x_0$ jest gwarantowany w pełni oceniony? | Naprawione | Stwierdzone wprost: rodzice i $x_0$ zawsze pochodzą z $\mathcal{H}_t$, nigdy z osobników ocenionych wyłącznie przez surogat | Proponowany Optymalizator |
| Granulacja przebudowy drzewa linkage (w obrębie sweepu vs. między rundami) | Naprawione | Stwierdzone wprost: stałe w obrębie iteracji, przebudowywane tylko w kroku 6 | Proponowany Optymalizator |
| Plan statystyczny: niezdefiniowany „pełny zbiór porównań” | Naprawione | Wyliczone: P3Net vs. każde z pozostałych dziewięciu ramion, osobno per benchmark i poziom budżetu | Wyniki, Plan statystyczny |
| Diagnostyka: duplication rate liczone przed czy po cache'u dedup? | Naprawione | Stwierdzone wprost: liczone w momencie propozycji, nie ewaluacji | Wyniki, Diagnostyka |
| Piramida P3 / „parameter-less” nigdy niewyjaśnione | Naprawione | Dodany jeden akapit przy pierwszym istotnym wprowadzeniu P3 | Prace pokrewne |
| „Few hundred” ewaluacji NSGANetV2 niedoprecyzowane, podczas gdy Wyniki cytują 350 | Naprawione | Prace pokrewne podają teraz dokładną liczbę (350) przy pierwszym wystąpieniu | Prace pokrewne |
| Uzasadnienie poziomów budżetu przywołujące rozbieżność benchmarków jako powód wyboru dwóch benchmarków | Naprawione | Usunięto kołowy fragment; wybór dwóch benchmarków uzasadniony raz, w Pracach pokrewnych (Kategoria 1/2), nie wtórnie z liczb budżetowych | Wyniki, Budżety |
| Fraza „in the spirit of eLyMPuS” powtórzona w trzech sekcjach | Odrzucone | Każde wystąpienie to krótki, lokalny gloss z odwołaniem w przód, nie dosłowna kopia bloku; usunięcie któregokolwiek przywróciłoby lukę forward-reference, którą miało zamykać | Wprowadzenie; Proponowany Optymalizator |
| Cytat trzech przeglądów systematycznych pojawiający się dwa razy w Pracach pokrewnych | Odrzucone | To nie duplikacja: oba fragmenty wyciągają dwa różne twierdzenia (dominujący paradygmat; brak linkage learning jako kategorii) z tych samych trzech przeglądów | Prace pokrewne |
| Brak jawnej hipotezy kierunkowej (H1) | Odrzucone | Pozostawione jako neutralne pytanie badawcze świadomie; konwencja GECCO, nie błąd | Wprowadzenie |
| Rejestr Wyników (tryb rozkazujący „must not allow”) | Odłożone | Wyniki to wciąż szkic protokołu; rejestr zostanie ujednolicony w finalnym przebiegu redakcyjnym, gdy szkic zastąpią prawdziwe liczby, nie iteracyjnie teraz | Wyniki |
| Sformułowanie „sanity baselines” | Odłożone | Preferencja terminologiczna niskiej wartości; zebrać w finalnym przebiegu redakcyjnym | Wyniki, Metody odniesienia |
| Zapowiedź diagnostyki duplication-rate we Wprowadzeniu | Naprawione (przy okazji) | Włączone do tej samej edycji, która złagodziła twierdzenie o korelacji duplicate-vs-interakcja, bo oba dotyczyły tego samego zdania | Wprowadzenie |
| „Mechanizm analogiczny do eLyMPuS” niedoprecyzowany (regresja vs. porównanie dyskretne) | Naprawione | Dodane rozróżnienie: mechanicznie bliżej CS-GOMEA (regresja różnicy ciągłej, brak gwarancji), filozoficznie bliżej eLyMPuS (relatywność, struktura odkrywana przyrostowo) | Prace pokrewne; Proponowany Optymalizator |
| Opis Zela i in. oraz lista hiperparametrów JAHS-Bench-201 zbyt ogólnikowe/niedokładne | Naprawione | Zela: pełna lista (metaparametry ResNet + 7 ciągłych HP); JAHS-Bench-201: usunięto błędnie dodany „optymalizator” z listy 4 hiperparametrów | Prace pokrewne |
| $r_K$ dla NAS-HPO-Bench-II: który poziom (12 czy 200 epok) faktycznie obowiązuje | Naprawione | Rozstrzygnięte wprost: $r_K$ ustalone na zakresie stablicowanym (12 epok); 200-epokowa ekstrapolacja nigdy nie odpytywana | Prace pokrewne; Wyniki |
| Czternastowymiarowa przestrzeń JAHS-Bench-201 przypisana samej przestrzeni przeszukiwania | Naprawione | Poprawione na dziesięć wymiarów przeszukiwania (6 architektura + 4 HP); czternaście dopiero po doliczeniu 4 wymiarów wierności, zgodnie z oryginalnym źródłem | Wyniki |
| Brak jawnego stwierdzenia o nieobecności operatora mutacji | Naprawione | Dodany osobny podnagłówek „Brak operatora mutacji” — cała wariacja to optimal mixing, dziedziczone po linii P3/GOMEA | Proponowany Optymalizator |
| Zbyt wiele mechanizmów w jednym akapicie (reprezentacja+drzewo+crossover; koszt+niewykonalność+dedup; cztery decyzje projektowe naraz) | Naprawione | Sekcja Proponowany Optymalizator rozbita na 11 nazwanych podnagłówków, jeden mechanizm na podnagłówek, analogicznie do struktury `results.tex` | Proponowany Optymalizator |
| Rodowód dawcy (donor) w kroku 1 pętli przeszukiwania | Otwarte | Rodzice i przodek $x_0$ mają jawne ograniczenie do $\mathcal{H}_t$, dawca — nie; oznaczone TODO w tekście, wymaga decyzji autorskiej | Proponowany Optymalizator |
| „Najlepszy znany front” (substytut IGD+ na benchmarkach bez oracle) niezdefiniowany | Otwarte | Oznaczone TODO z proponowaną definicją (unia punktów ze wszystkich metod/przebiegów) do potwierdzenia | Wyniki |
| „Drzewo rozpinające (MST)” w Podsumowaniu niezgodne z UPGMA opisanym w Proponowanym Optymalizatorze | Naprawione | Poprawiona terminologia: drzewo powiązań oparte na informacji wzajemnej, nie MST | Podsumowanie |
| Diagram pętli przeszukiwania P3Net | Dodane (tylko LaTeX) | Diagram TikZ w `chapters/v003/proposed_optimizer/main.tex`; wersja Markdown odsyła do niego cross-referencją zamiast duplikować w ASCII | Proponowany Optymalizator |
