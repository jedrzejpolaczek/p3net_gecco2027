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

Przeszukiwanie architektur sieci neuronowych (NAS) eksploruje duże, dyskretne przestrzenie kandydackich projektów sieci, a ocena pojedynczego kandydata względem prawdziwego celu — czy to poprzez trenowanie od zera, poprzez współdzielenie wag, czy poprzez odpytanie benchmarku zbudowanego w tym celu — stanowi dominujący koszt przeszukiwania. Powszechną praktyką jest traktowanie przeszukiwania architektury i strojenia hiperparametrów jako dwóch odrębnych etapów — najpierw przeszukiwanie architektury przy ustalonym lub domyślnym zestawie hiperparametrów, a następnie strojenie hiperparametrów dla zwycięskiej architektury. Zela i in. \citep{zela2018towards} pokazują, że takie podejście jest zawodne z dwóch powodów: architektura i hiperparametry wzajemnie na siebie oddziałują, więc najlepsza architektura przy jednym zestawie hiperparametrów niekoniecznie jest najlepsza przy innym; a powszechnie stosowany skrót polegający na rankingowaniu architektur po zaledwie kilku epokach treningu słabo koreluje z ich rankingiem przy pełnym budżecie treningowym. Rozdzielenie tych dwóch etapów podwaja to ryzyko. Wspólne przeszukiwanie obu wymiarów, zamiast sekwencyjnego, pozwala uniknąć tego kumulowania się ryzyka, kosztem dodatkowego powiększenia i tak już kosztownej przestrzeni przeszukiwania.

NSGA-Net \citep{lu2019nsganet} ustanowił przeszukiwanie ewolucyjne prowadzone bezpośrednio nad architekturami sieci, trenując każdego kandydata do końca. NSGANetV2 \citep{lu2020nsganetv2} pokazał, że połączenie tego samego silnika ewolucyjnego z wyuczonym predyktorem dokładności pozwala tanio przesiać większość kandydatów, rezerwując pełną ewaluację dla niewielkiego, obiecującego podzbioru; ten wzorzec wspomagany predyktorem zastępczym (surrogate) jest obecnie dominującym paradygmatem w ewolucyjnym NAS.

Własne eksperymenty autorów NSGA-Net sugerują, że ta ukryta struktura zależności nie jest bez znaczenia: 60–80% wygenerowanych genotypów dekoduje się do zduplikowanych architektur w miarę wzrostu liczby węzłów \citep{lu2019nsganet} — dowód na to, że zmienne w kodowaniu wzajemnie oddziałują w sposób, który operator niewidzący tej struktury może wykorzystać co najwyżej przypadkowo, jeśli w ogóle. Osobny nurt badań, ewolucyjne algorytmy uczące powiązania (linkage learning) takie jak GOMEA \citep{thierens2011optimal} oraz Bezparametrowa Piramida Populacji (Parameter-less Population Pyramid, P3) \citep{goldman2014parameterless}, rozwijany w dużej mierze niezależnie od tej opartej na NSGA-II linii badań nad NAS, celuje dokładnie w ten problem: uczy się, które zmienne genotypu wzajemnie oddziałują, i chroni te grupy podczas krzyżowania, zamiast traktować genotyp jako nieustrukturyzowane kodowanie, co w zamyśle pozwala uniknąć tego rodzaju redundantnego, generującego duplikaty przeszukiwania, jakie dokumentują własne wyniki liczbowe NSGA-Net. Generowanie duplikatów i istotne dla dopasowania (fitness) oddziaływanie zmiennych są ze sobą powiązane, lecz stanowią odrębne zjawiska: pierwsze jest właściwością wyłącznie funkcji dekodującej, drugie — tego, jak zmienne genotypu wspólnie determinują wartość celu. Operator świadomy zależności celuje w to drugie zjawisko. To, czy ogranicza on również pierwsze — czy redundancja dekodowania w praktyce koreluje ze strukturą powiązań (linkage) odkrywaną przez P3 — jest pytaniem empirycznym, a nie założeniem; diagnostyka wskaźnika duplikacji w sekcji Wyniki testuje to bezpośrednio w ramach wspólnego genotypu.

P3Net łączy te dwie dźwignie. Zastępuje NSGA-II algorytmem P3 jako silnikiem przeszukiwania, dzięki czemu krzyżowanie podąża za drzewem powiązań (linkage tree) wyuczonym na podstawie populacji, zamiast działać na pojedynczych zmiennych, i łączy go z predyktorem zastępczym, który jest relatywny i świadomy struktury powiązań: zamiast regresji bezwzględnej dokładności kandydata na podstawie jego pełnego kodowania, przewiduje on zmianę dokładności względem rodzica, ograniczoną do jednego zmodyfikowanego podzbioru powiązań, w duchu eLyMPuS — wariantu LyMPuS \citep{przewozniczek2026lympus}, który przewiduje względną zmianę dopasowania (fitness) wzdłuż struktury powiązań odkrywanej przyrostowo, a nie zakładanej jako znana z góry (rozwinięcie w sekcji Prace pokrewne). Zarówno silnik przeszukiwania, jak i predyktor zastępczy są rozszerzone do ustawienia wspólnego, w którym genotyp obejmuje, obok wyborów architektonicznych, również hiperparametry treningowe, takie jak współczynnik uczenia (learning rate) i zanik wag (weight decay).

Pytanie badawcze i wkład pracy: czy przy ustalonym, ograniczonym budżecie pełnych ewaluacji, przeszukiwanie P3 świadome zależności, połączone z relatywnym predyktorem zastępczym świadomym struktury powiązań, wytwarza kandydatów o lepszym kompromisie między dokładnością a kosztem obliczeniowym niż selekcja oparta na odległości zagęszczenia (crowding distance) NSGA-II połączona z bezwzględnym predyktorem regresyjnym, tak jak w NSGANetV2? Testujemy to w ustawieniu wspólnego przeszukiwania architektury i hiperparametrów. Dopasowane badania ablacyjne rozdzielają obie dźwignie — silnik przeszukiwania i predyktor zastępczy — na tyle, na ile pozwala na to konstrukcja eksperymentu; relatywny predyktor zastępczy świadomy struktury powiązań jest zdefiniowany wyłącznie przy danym drzewie powiązań, więc nie może zostać połączony z NSGA-II, a sekcja Wyniki szczegółowo omawia to ograniczenie konstrukcji badań ablacyjnych. Odpowiadamy na to pytanie za pomocą P3Net: ewolucyjnego algorytmu uczącego powiązania połączonego z relatywnym predyktorem zastępczym świadomym struktury powiązań do wspólnego przeszukiwania architektury i hiperparametrów, ocenionego poprzez kontrolowane porównanie z NSGANetV2 oraz tymi dopasowanymi badaniami ablacyjnymi, przy równych budżetach pełnych ewaluacji, na dwóch wspólnych benchmarkach — JAHS-Bench-201 oraz NAS-HPO-Bench-II. Najbliższa wcześniejsza praca łączy już algorytm ewolucyjny uczący powiązania wspomagany predyktorem zastępczym z przeszukiwaniem sieci, lecz w przestrzeni obejmującej wyłącznie architekturę \citep{bartnik2026evolutionary}; sekcja Prace pokrewne szczegółowo omawia, czym relatywny predyktor zastępczy P3Net świadomy struktury powiązań, jego bezpośrednie porównanie z NSGA-II/NSGANetV2 oraz jego zakres obejmujący wspólne przeszukiwanie architektury i hiperparametrów różnią się od tego punktu odniesienia.

---

## Prace pokrewne

Przeszukiwanie ewolucyjne architektur bez wspomagania predyktorem zastępczym zapoczątkował NSGA-Net \citep{lu2019nsganet}, który wykorzystuje NSGA-II jako silnik przeszukiwania architektur sieci konwolucyjnych, z selekcją opartą na sortowaniu niezdominowanym i odległości zagęszczenia (crowding distance). Każdy kandydat w tym podejściu przechodzi pełny trening, a jedynym mechanizmem przyspieszającym zbieżność jest wykorzystanie historii przeszukiwania za pomocą sieci bayesowskiej. Warto odnotować, że autorzy dokumentują znaczącą redundancję na drodze od genotypu do fenotypu, raportując, że 60–80% wygenerowanych genotypów odpowiada zduplikowanym architekturom w miarę wzrostu liczby węzłów, co wskazuje na nietrywialną, nieliniową strukturę zależności ukrytą w kodowaniu architektury.

Rok później NSGANetV2 \citep{lu2020nsganetv2} wprowadził predyktor dokładności doskonalony na bieżąco w trakcie przeszukiwania i zastąpił pełny trening od zera dostrajaniem (fine-tuningiem) wag odziedziczonych z supersieci (supernet), zmniejszając liczbę w pełni ewaluowanych architektur do 350 (Tabela 2 oryginalnego opracowania) — zamiana ta wymienia koszt treningu na udokumentowane ryzyko niezgodności rankingów między dokładnością uzyskaną przy współdzieleniu wag a dokładnością uzyskaną z niezależnego treningu \citep{yu2020evaluatingnas}. Ten schemat, łączący NSGA-II z wyuczonym predyktorem zastępczym, pozostaje dominującym paradygmatem w wielokryterialnym NAS, co niezależnie potwierdzają trzy systematyczne przeglądy literatury \citep{liu2023survey, white2023insights, ozcelik2026survey}. Dalszy rozwój w tym kierunku skierował się ku predyktorom opartym na rankingowaniu zamiast regresji, takim jak RankNet w MoSegNAS \citep{lu2022mosegnas}, który rozszerza podejście NSGANetV2 na segmentację semantyczną, a także ku krytycznej ponownej ocenie tzw. proxy zerokosztowych (zero-cost proxies), których udokumentowaną słabością jest niewiarygodne rozróżnianie architektur znajdujących się na szczycie rankingu.

Równolegle rozwinęła się odrębna rodzina algorytmów ewolucyjnych, która jawnie modeluje strukturalne zależności między zmiennymi genotypu, a mianowicie GOMEA \citep{thierens2011optimal} oraz Bezparametrowa Piramida Populacji (P3) \citep{goldman2014parameterless}. Algorytmy te budują drzewo powiązań na podstawie zależności statystycznych obserwowanych w populacji i wykorzystują je do kierowania krzyżowaniem, chroniąc wykryte grupy zależnych zmiennych przed zaburzeniem. P3 dodatkowo przeciwdziała przedwczesnej zbieżności typowej dla modeli generacyjnych: w odróżnieniu od NSGA-II nie odrzuca wcześniej znalezionych dobrych rozwiązań, jednocześnie wprowadzając nową różnorodność. Strukturalnie P3 zastępuje pojedynczą populację o stałym rozmiarze uporządkowaną piramidą populacji o rosnącym rozmiarze, dodając nowy poziom dopiero wtedy, gdy istniejące poziomy przestają dawać lepsze rozwiązania — jest to właściwość, do której odnosi się nazwa „bezparametrowa” (parameter-less), ponieważ rozmiar populacji nie jest wybierany z góry \citep{goldman2014parameterless}. Zbudowanie i przesunięcie pojedynczego nowego rozwiązania w górę piramidy w standardowym ujęciu wymaga rzeczywistej ewaluacji dopasowania (fitness) przy każdej zaakceptowanej lokalnej poprawie, a nie tylko na końcu procesu; ten szczegół ma bezpośrednie znaczenie dla rozliczania budżetu przy niewielkich budżetach ewaluacji stosowanych w P3Net (sekcja Wyniki wraca do tego przy omawianiu wariantu ablacyjnego P3 bez predyktora zastępczego).

Warto zaznaczyć, że opisane powyżej powiązania (linkage) uczone statystycznie na poziomie populacji nie powinny być mylone z optymalizacją gray-box w węższym sensie, ustanowionym przez Whitleya, Chicano i Goldmana \citep{whitley2016graybox} i stosowanym od tamtej pory w nurcie prac nad GOMEA, w tym w jego rozszerzeniu rzeczywistoliczbowym RV-GOMEA \citep{andreadis2024maxclique} oraz we wspólnej bibliotece GOMEA \citep{bouter2023library}. W tamtym ujęciu optymalizator otrzymuje jawny dostęp do podfunkcji składających się na funkcję celu i wykorzystuje ten dostęp do wykonywania taniej, częściowej ponownej ewaluacji dopasowania po zlokalizowanej zmianie zmiennej. Niniejsza praca działa natomiast w reżimie black-box: dokładności walidacyjnej NAS nie da się rozłożyć na lokalnie przeliczalne podfunkcje, więc P3 pełni tu wyłącznie rolę silnika przeszukiwania świadomego struktury zależności genotypu, podczas gdy redukcja kosztu jest osiągana za pomocą omawianego dalej wyuczonego predyktora zastępczego.

Podobnie jak w przypadku NSGA-Net i NSGANetV2, koszt pełnej ewaluacji pozostaje głównym wąskim gardłem także dla ewolucyjnych algorytmów uczących powiązania: każdy krok optymalnego mieszania (optimal mixing) proponuje częściową zmianę zmiennej, której wpływ na funkcję celu musi, w opisanym powyżej reżimie black-box, zostać zweryfikowany poprzez pełną ewaluację dopasowania. Połączenie tego silnika przeszukiwania z tanim, wyuczonym predyktorem zastępczym, który przesiewa kandydatów przed podjęciem decyzji o pełnej ewaluacji, jest zatem naturalnym rozszerzeniem.

Łączenie algorytmów uczących powiązania z wyuczonym predyktorem zastępczym było już badane, choć nie w dziedzinie NAS. CS-GOMEA \citep{dushatskiy2019csgomea} integruje GOMEA z konwolucyjną siecią neuronową pełniącą rolę predyktora zastępczego, ocenianą na syntetycznych problemach kombinatorycznych (Onemax, funkcje Trap, krajobrazy NK, HIFF); autorzy jawnie wskazują niewykorzystanie przez predyktor zastępczy informacji z drzewa powiązań przy jego własnej konstrukcji jako otwarty kierunek badawczy. Dushatskiy, Alderliesten i Bosman \citep{dushatskiy2021novelsurrogateassistedevolutionaryalgorithm} integrują predyktor zastępczy bezpośrednio z wariantem P3 — pierwszy udokumentowany taki przypadek — testując podejście na kosztownym, rzeczywistym problemie uczenia zespołowego (ensemble learning) opartego na partycjonowaniu; warto odnotować, że w ich eksperymentach model SVR przewyższył predyktor neuronowy. Najnowsza praca w tym nurcie, LyMPuS \citep{przewozniczek2026lympus}, wprowadza predyktor zastępczy zintegrowany bezpośrednio z mechanizmem odkrywania powiązań i weryfikuje go eksperymentalnie w połączeniu z P3, ponownie na klasycznych benchmarkach kombinatorycznych, takich jak krajobrazy NK, szkła spinowe Isinga (Ising Spin Glasses) i Max3Sat. Predyktor zastępczy P3Net opiera się konkretnie na eLyMPuS — „empirycznej” wersji LyMPuS, wprowadzonej w tej samej pracy — który zastępuje założenie LyMPuS o znanej prawdziwej strukturze zależności strukturą zależności odkrywaną przyrostowo i potencjalnie niekompletnie, dostępną w ustawieniu black-box — dokładnie w takim reżimie działa P3Net; sekcja Proponowany Optymalizator szczegółowo opisuje tę adaptację.

Wśród zastosowań algorytmów uczących powiązania bezpośrednio do NAS, które całkowicie rezygnują z wyuczonego predyktora zastępczego, jedyną zidentyfikowaną pracą jest praca Trana, Truonga, Vo i Luonga \citep{tran2023gomeanas}, łącząca GOMEA z Synaptic Flow — metryką nie wymagającą treningu, obliczaną analitycznie i niewymagającą uczenia się na podstawie wcześniejszych wyników ewaluacji. Stanowi to fundamentalnie odmienny mechanizm redukcji kosztu niż wyuczony predyktor zastępczy i, jak omówiono poniżej, różni się od wspomaganego predyktorem zastępczym uczenia powiązań zastosowanego do NAS przez Bartnik \citep{bartnik2026evolutionary}.

Niezależnie od podejść opartych na uczeniu powiązań, węższy nurt prac zajął się wspólną optymalizacją architektury sieci i hiperparametrów treningowych, zamiast traktować strojenie hiperparametrów jako odrębny krok następujący po przeszukiwaniu architektury \citep{zela2018towards}. Od tego czasu wprowadzono ustandaryzowane benchmarki dla tego ustawienia, mianowicie JAHS-Bench-201 \citep{bansal2022jahsbench} — benchmark oparty na predyktorze zastępczym nad wspólną przestrzenią przeszukiwania łączącą zmienne kategoryczne i ciągłe, oraz NAS-HPO-Bench-II \citep{hirose2021nashpobenchii} — tablicę przeglądową (lookup table) opartą na stałej siatce kombinacji architektury i hiperparametrów. Systematyczne porównanie solverów w tym ustawieniu \citep{guerreroviu2021bagofbaselines} ocenia standardowe metody odniesienia, takie jak NSGA-II, wielokryterialna bayesowska optymalizacja Hyperband (MO-BOHB) oraz przeszukiwanie losowe; żadna z metod porównywanych w tym nurcie prac nie jest ewolucyjnym algorytmem uczącym powiązania.

W całej literaturze dotyczącej wspólnego NAS+HPO, hiperparametryczna połowa przestrzeni przeszukiwania konsekwentnie dotyczy procedury treningowej, a nie strukturalnej pojemności sieci. JAHS-Bench-201 \citep{bansal2022jahsbench} przeszukuje jako hiperparametry współczynnik uczenia, zanik wag, optymalizator, funkcję aktywacji i augmentację danych, podczas gdy liczba komórek i szerokość kanałów są traktowane jako odrębna oś wierności (fidelity) obok liczby epok treningu i rozdzielczości wejścia, odrębna zarówno od wymiaru architektury, jak i hiperparametrów. NAS-HPO-Bench-II \citep{hirose2021nashpobenchii} zmienia jako hiperparametry jedynie współczynnik uczenia i rozmiar batcha, w oparciu o ustaloną przestrzeń przeszukiwania topologii komórki, przy czym czas trwania treningu jest obsługiwany przez osobny predyktor zastępczy, a nie jako przeszukiwana zmienna. Zela i in. \citep{zela2018towards} podobnie wspólnie optymalizują operacje komórki razem ze współczynnikiem uczenia, zanikiem wag, rozmiarem batcha i regularyzacją, wykorzystując liczbę epok treningu wyłącznie jako wymiar zasobu w Hyperbandzie, a nie jako zmienną decyzyjną. P3Net stosuje się do tej samej konwencji: rozszerzenie genotypu dla ustawienia wspólnego dodaje hiperparametry procedury treningowej, takie jak współczynnik uczenia i zanik wag, podczas gdy wybory dotyczące pojemności strukturalnej pozostają częścią właściwego kodowania architektury. Bartnik \citep{bartnik2026evolutionary} całkowicie omija tę kwestię projektową, ponieważ jej genotyp w ogóle nie ma wymiaru hiperparametrów: procedura treningowa jest ustalona przez tablicę przeglądową NAS-Bench-201, a jej własna dyskusja przyznaje, że wynikające z tego wnioski opisują tę zamkniętą przestrzeń przeszukiwania, a nie NAS w ogólności — ograniczenie, które bezpośrednio motywuje ewaluację na rzeczywiście wspólnych benchmarkach, takich jak wymienione powyżej.

Przeanalizowana powyżej literatura dotycząca wspólnego NAS+HPO różni się również pod względem tego, co dostarcza prawdę odniesienia (ground truth) dla ewaluacji. Zela i in. \citep{zela2018towards} optymalizują ustawienie wspólne za pomocą BOHB na rzeczywistych przebiegach treningowych. NAS-HPO-Bench-II \citep{hirose2021nashpobenchii} oraz JAHS-Bench-201 \citep{bansal2022jahsbench}, w przeciwieństwie do tego, odpowiadają na każde zapytanie odpowiednio przez stałą tablicę przeglądową lub wyuczony predyktor zastępczy, bez rzeczywistego treningu w chwili ewaluacji. Benchmarki pierwszego rodzaju, z ustaloną, wyczerpująco enumerowalną tablicą przeglądową, nad którą można w związku z tym obliczyć dokładny front Pareto (oracle), określamy jako *Kategorię 1*, a benchmarki drugiego rodzaju, które odpowiadają na każde zapytanie za pomocą wyuczonego, ciągłego predyktora zastępczego nad przestrzenią przeszukiwania i nie dopuszczają enumerowalnego frontu oracle, określamy jako *Kategorię 2*; w tej terminologii NAS-HPO-Bench-II należy do Kategorii 1, a JAHS-Bench-201 do Kategorii 2. Głównymi benchmarkami P3Net są właśnie te dwa, wybrane z powodów już ustalonych w tym nurcie badań oraz szerzej w literaturze NAS Kategorii 1: deterministyczna funkcja celu, obliczalny front oracle oraz ograniczony budżet ewaluacji.

Ten predyktor zastępczy na poziomie benchmarku nie powinien być mylony z wyuczonym predyktorem zastępczym, który P3Net, CS-GOMEA \citep{dushatskiy2019csgomea}, Dushatskiy i in. \citep{dushatskiy2021novelsurrogateassistedevolutionaryalgorithm} oraz LyMPuS \citep{przewozniczek2026lympus} budują w trakcie samego przeszukiwania. Predyktor zastępczy JAHS-Bench-201 zastępuje funkcję celu jednorazowo, offline, zanim rozpocznie się jakiekolwiek przeszukiwanie; predyktor zastępczy działający w czasie przeszukiwania, stosowany przez te metody uczące powiązania, jest natomiast dopasowywany przyrostowo na podstawie już ewaluowanych kandydatów, wyłącznie w celu podjęcia decyzji, którzy kolejni kandydaci zasługują na pełne zapytanie. Te dwie role stanowią niezależne decyzje projektowe, a wkład P3Net dotyczy wyłącznie drugiej z nich, nałożonej na dowolne podłoże (substrate) odpowiadające za pełną ewaluację.

Najbliższa niniejszej pracy jest praca Bartnik \citep{bartnik2026evolutionary}, która adaptuje SA-P3-GOMEA — algorytm uczący powiązania wspomagany predyktorem zastępczym — do wielokryterialnego NAS na NAS-Bench-201, optymalizując dokładność walidacyjną względem zmierzonego zużycia energii przez GPU. Zastosowany tam predyktor zastępczy jest bezwzględnym regresorem nad płaskim genotypem (deterministyczne lub probabilistyczne warianty SVR, MLP, lasu losowego lub gradient boostingu), porównywanymi metodami odniesienia są MO-LS oraz pozbawiony predyktora zastępczego MO-P3-GOMEA, a nie NSGA-II czy NSGANetV2, a przestrzeń przeszukiwania to zamknięty benchmark NAS-Bench-201 ograniczony wyłącznie do architektury, bez żadnych hiperparametrów treningowych w genotypie.

Trzy niezależne systematyczne przeglądy literatury dotyczącej ewolucyjnego NAS \citep{liu2023survey, white2023insights, ozcelik2026survey} nie wymieniają GOMEA, P3 ani uczenia powiązań szerzej jako odrębnej kategorii metod, co wskazuje, że ta rodzina algorytmów pozostaje poza głównym nurtem dziedziny. Choć połączenie ewolucyjnego algorytmu uczącego powiązania z wyuczonym predyktorem zastępczym zostało już zweryfikowane empirycznie, a praca Bartnik rozszerza je na NAS, trzy aspekty pozostają wspólnie nierozwiązane: relatywny predyktor zastępczy świadomy struktury powiązań zamiast bezwzględnego regresora nad płaskim genotypem; NSGA-II/NSGANetV2 jako bezpośrednio porównywana metoda odniesienia; oraz wspólne przeszukiwanie architektury i hiperparametrów, do którego, zgodnie z naszą wiedzą, żaden ewolucyjny algorytm uczący powiązania nie był wcześniej stosowany.

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
W ustawieniu wspólnego przeszukiwania architektury i hiperparametrów, będącym celem sekcji Wyniki, $\Lambda$
jest rozszerzona o ciągłe współrzędne odpowiadające hiperparametrom treningowym (np.\ współczynnik uczenia, zanik wag),
co daje $\Lambda = \Lambda_1 \times \cdots \times \Lambda_n \times \Theta$, gdzie $\Theta \subset \mathbb{R}^m$
gromadzi te ciągłe współrzędne. Otwarte pozostają dwa sposoby rozwiązania problemu, w jaki sposób blokowe krzyżowanie
oparte na drzewie powiązań P3, zdefiniowane nad dyskretnymi grupami, ma obsługiwać $\Theta$; oba są zgodne z poniższym
sformułowaniem: (i) dyskretyzacja każdej współrzędnej $\Theta$ do zbioru skończonego, wchłaniająca ją do powyższego
dyskretnego iloczynu bez zmiany operatora krzyżowania, lub (ii) rozszerzenie drzewa powiązań i optymalnego mieszania
o mieszanie rzeczywistoliczbowe na $\Theta$ w duchu RV-GOMEA \citep{andreadis2024maxclique}, obok dyskretnego mieszania
na $\Lambda_1 \times \cdots \times \Lambda_n$. Wybór jednego z tych dwóch podejść jest ustalany jednorazowo, w sekcji
Proponowany Optymalizator; żaden z wyborów nie zmienia zdefiniowanych poniżej $D$, $g$, $f_1$ ani $f_2$.

**Dekodowanie i poprawność.**
Funkcja dekodująca $D \colon \Lambda \to \mathcal{N}$ odwzorowuje genotyp na sieć neuronową.
Nie każdy genotyp daje w wyniku poprawną architekturę (np.\ nie istnieje ścieżka między wejściem a wyjściem komórki).
Ograniczenie poprawności wyrażamy jako
\[
    g(x) \leq 0,
\]
gdzie $g \colon \Lambda \to \mathbb{R}$ jest funkcją strukturalną -- boolowską w przypadkach rozważanych w tej pracy
(np.\ $g(x) \in \{-1, +1\}$ kodujące istnienie ścieżki wejście–wyjście), lecz zapisaną w postaci rzeczywistoliczbowej,
by uwzględnić stopniowaną miarę niedopuszczalności, gdyby jakiś benchmark taką definiował; $x$ jest *poprawny*
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
Optymalizator). Żadna z metod porównywanych w sekcji Wyniki (Metody odniesienia) również jej nie wykorzystuje;
definiujemy ją tutaj jako ogólny mechanizm na poziomie podłoża (substrate) -- przydatny, gdyby do porównania miała
zostać w przyszłości dodana metoda odniesienia wielopoziomowa (np.\ oparta na Hyperbandzie) -- a nie jako aktywny
składnik obecnego eksperymentu.

**Szum ewaluacji.**
Tam, gdzie podłoże odpowiadające za $f_1$ niesie ze sobą rzeczywistą stochastyczność, na przykład rzeczywisty trening
lub własne zarejestrowane powtórzenia benchmarku, $f_1^{(k)}(x)$ jest traktowane jako zmienna losowa: każda
konfiguracja jest ewaluowana z użyciem $s$ różnych ziaren losowości (seedów) lub próbek pobranych z zarejestrowanych
powtórzeń podłoża, a do selekcji i raportowania wykorzystywana jest mediana z nich. Podłoża deterministyczne, takie
jak predyktor zastępczy dający pojedynczy punktowy estymat, nie wymagają takiego uśredniania. Oba główne benchmarki
P3Net (Wyniki) odpowiadają na zapytania deterministycznie -- predyktor zastępczy dający pojedynczy estymat dla
JAHS-Bench-201, stała tablica przeglądowa dla NAS-HPO-Bench-II -- więc w całej tej pracy $s=1$, a ten krok uśredniania
nie jest wykorzystywany; jest on zachowany jako ogólny mechanizm na poziomie podłoża z myślą o przyszłych pracach nad
podłożami stochastycznymi, takimi jak rzeczywisty trening. $s$ nie należy mylić z $R$ -- liczbą niezależnych przebiegów
przeszukiwania na metodę (Wyniki): $R$ pozostaje istotne niezależnie od determinizmu podłoża, ponieważ losowość między
przebiegami wynika z inicjalizacji i stochastycznych operatorów przeszukiwania, a nie z powtarzanych zapytań o tę samą
konfigurację.

**Model predyktora zastępczego.**
Pełna ewaluacja $f_1(x)$ odpytuje prawdziwą funkcję celu dla $D(x)$; konkretne podłoże tego zapytania -- czy to
rzeczywisty trening, tablica przeglądowa benchmarku, czy własny predyktor zastępczy benchmarku -- jest skonkretyzowane
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

P3Net generuje kandydatów za pomocą P3 zamiast NSGA-II. Drzewo powiązań budowane jest na podstawie bieżącej populacji
i odzwierciedla zależności statystyczne między zmiennymi genotypu, tj.\ wyborami operacji na poszczególnych krawędziach
z sekcji Sformułowanie Problemu. Zgodnie ze standardową procedurą P3, drzewo konstruowane jest za pomocą aglomeracyjnego
grupowania hierarchicznego w stylu UPGMA nad znormalizowaną miarą zależności opartą na informacji wzajemnej między
zmiennymi genotypu, dając zagnieżdżoną rodzinę podzbiorów zmiennych wykorzystywaną przez operator optymalnego mieszania;
konstrukcja ta jest stosowana do genotypu NAS bez zmian względem jego pierwotnej postaci optymalizacji kombinatorycznej.
P3Net przyjmuje opcję (i) z sekcji Sformułowanie Problemu: każda ciągła współrzędna $\Theta$ jest dyskretyzowana do
skończonego zbioru przedziałów (binów), ustalonego jednorazowo przed rozpoczęciem przeszukiwania (np.\ siatka
logarytmiczna dla współczynnika uczenia), tak że wspólny genotyp $\Lambda_1 \times \cdots \times \Lambda_n \times \Theta$
jest w całości kategoryczny, a drzewo powiązań, jego oparta na informacji wzajemnej miara zależności oraz opisane
poniżej przemiatanie optymalnego mieszania stosują się do niego dokładnie tak samo, jak do kodowania obejmującego
wyłącznie architekturę, bez odrębnego mechanizmu mieszania rzeczywistoliczbowego. Takie podejście wymienia rozdzielczość
ciągłego przeszukiwania hiperparametrów na utrzymanie centralnego porównania z NSGA-II/NSGANetV2 przypisywalnego
wyłącznie silnikowi przeszukiwania i predyktorowi zastępczemu, zamiast mieszać je z dodatkowym, odrębnie nowatorskim
rozszerzeniem P3 o mieszanie rzeczywistoliczbowe; rozszerzenie do opcji (ii) (mieszanie rzeczywistoliczbowe w duchu
RV-GOMEA \citep{andreadis2024maxclique}) pozostawiono jako przyszłą pracę. Krzyżowanie działa na poziomie grup zmiennych
zidentyfikowanych przez to drzewo, a nie na poziomie pojedynczych bitów, chroniąc wykryte grupy powiązanych decyzji
projektowych przed zaburzeniem.

Konstrukcja predyktora zastępczego w P3Net wykorzystuje tę samą strukturę zależności, która kieruje operatorem
wariacji: relatywny estymator $\hat{\delta}_F$ świadomy struktury powiązań, zdefiniowany w sekcji Sformułowanie
Problemu, wytrenowany na parowych różnicach dopasowania wyprowadzonych z $\mathcal{H}_t$, jest tym, co przemiatanie
optymalnego mieszania P3 odpytuje przy każdej proponowanej modyfikacji -- mechanizm analogiczny do eLyMPuS, wariantu
LyMPuS \citep{przewozniczek2026lympus}, który przewiduje relatywną zmianę dopasowania warunkowaną niekompletnie
odkrytą strukturą powiązań (rozwinięcie w sekcji Prace pokrewne), zaadaptowany tutaj do kodowania architektury sieci.
Estymatę bezwzględnego błędu kandydata uzyskuje się kompozycyjnie, poprzez teleskopowe cofnięcie tej relatywnej
korekty wzdłuż przemiatania do najbliższego przodka o znanej, w pełni ewaluowanej wartości $f_1$: zapisując
$x_0, x_1, \dots, x_m = x'$ jako łańcuch tymczasowo zaakceptowanych modyfikacji od tego przodka $x_0$ (przy znanym
$f_1(x_0)$), przy czym każdy krok wnosi $\hat{\delta}_{F_i}(x_{i-1}, x_i)$ dla podzbioru powiązań $F_i$
zmodyfikowanego w kroku $i$,
\[
    \hat{f}_1(x_m) = f_1(x_0) - \sum_{i=1}^{m} \hat{\delta}_{F_i}(x_{i-1}, x_i),
\]
co sprowadza się do $\hat{f}_1(x') = f_1(x) - \hat{\delta}_F(x, x')$ w przypadku pojedynczego kroku $m=1$. Głębokość
łańcucha $m$ jest ograniczona przez $\kappa$, wprowadzone poniżej, właśnie po to, by ograniczyć, jak daleko może się
propagować skumulowany błąd predyktora zastępczego, zanim zresetuje go pełna ewaluacja.

Pętla przeszukiwania przebiega następująco:

1. P3 generuje zbiór kandydatów $C \subset \Lambda^*$ poprzez krzyżowanie kierowane drzewem powiązań; dla każdego
   rodzica wybranego do wariacji, każdy podzbiór powiązań w bieżącym modelu zależności jest odwiedzany w losowej
   kolejności, zgodnie ze standardowym przemiataniem optymalnego mieszania, a dla każdego podzbioru $F$ z populacji
   losowany jest dawca, proponujący modyfikację ograniczoną do $F$;
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

Rodzice dla kroku 1, a także przodek $x_0$ wykorzystywany w opisanej powyżej konstrukcji teleskopowej, są zawsze
losowani spośród osobników, które ukończyły kroki 5–6 -- tj.\ elementów $\mathcal{H}_t$ o rzeczywiście znanej wartości
$f_1$ -- nigdy spośród przejściowych, opartych wyłącznie na predyktorze zastępczym osobników powstałych w trakcie
przemiatania; konstrukcja teleskopowa nigdy więc nie kończy się na estymacie predyktora zastępczego.

P3Net działa wyłącznie przy pełnej wierności $r_K$: aparat niższej wierności wprowadzony w sekcji Sformułowanie
Problemu jest mechanizmem na poziomie podłoża, konkretyzowanym tam, gdzie ma to zastosowanie, w sekcji Wyniki, lecz
nie jest wykorzystywany przez opisaną powyżej pętlę przeszukiwania. Trenowanie predyktora zastępczego również na
obserwacjach o niższej wierności jest alternatywą projektową omówioną w Podsumowaniu.

Koszt obliczeniowy $f_2$ jest obliczany analitycznie, bez udziału predyktora zastępczego, więc selekcja kandydatów
do pełnej ewaluacji opiera się na niezdominowaniu w przestrzeni $(\hat{f}_1, f_2)$. Kandydaci naruszający ograniczenie
$g(x) \leq 0$ są odrzucani przed oceną przez predyktor zastępczy, a duplikaty już obecne w $\mathcal{H}_t$ pomijają
ponowną ewaluację -- stosowane identycznie do każdej porównywanej metody w ramach wspólnej infrastruktury ewaluacyjnej
(Wyniki, Kontrole rzetelności), więc ta oszczędność nie jest specyficzna dla P3Net -- zabezpieczenie o istotnym
praktycznym znaczeniu, biorąc pod uwagę udokumentowaną w NSGA-Net (Wprowadzenie) redundancję na drodze od genotypu do
fenotypu \citep{lu2019nsganet}.

Z adaptacji mechanizmu eLyMPuS do tego ustawienia wynikają cztery decyzje projektowe. Po pierwsze, generowanie
kandydatów podąża za pełnym przemiataniem optymalnego mieszania opisanym w kroku 1, zamiast pojedynczej modyfikacji
na kandydata, dzięki czemu P3Net pozostaje spójny z operatorem wariacji, na którym opierają się własne gwarancje
skuteczności P3. Po drugie, gwarancja eLyMPuS odtworzenia brakującej zależności w ciągu $2\lceil\log_2(n)\rceil$
kroków opiera się na założeniu monotoniczności leżącego u podstaw krajobrazu dopasowania, którego nie oczekuje się
w przypadku dokładności sieci neuronowej; $\hat{\delta}_F$ jest zatem traktowana jako wyuczony estymator
heurystyczny bez tej gwarancji, a jej wiarygodność jest zamiast tego oceniana empirycznie poprzez analizę jakości
predyktora zastępczego zaraportowaną w sekcji Wyniki. Po trzecie, aby ograniczyć akumulację błędu predyktora
zastępczego wzdłuż przemiatania, narzucona jest maksymalna głębokość łańcucha $\kappa$ tymczasowo zaakceptowanych
modyfikacji opartych wyłącznie na predyktorze zastępczym: gdy tylko wzdłuż danego przemiatania od ostatniej pełnej
ewaluacji zaakceptowano $\kappa$ modyfikacji, bieżący osobnik jest wymuszany do $C^*$ niezależnie od jego
przewidywanego $\hat{f}_1$. $\kappa$ jest inicjalizowana wartością własnej granicy eLyMPuS wynoszącej
$2\lceil\log_2(n)\rceil$ kroków (powyżej) -- gdzie $n$ jest wymiarem pełnego, rozszerzonego, zdyskretyzowanego
genotypu $\Lambda_1 \times \cdots \times \Lambda_n \times \Theta$, odpowiadającym zakresowi samego drzewa powiązań,
a nie liczbie uwzględniającej wyłącznie architekturę z sekcji Sformułowanie Problemu -- jako domyślna wartość
heurystyczna -- a nie jako wyprowadzenie z gwarancji monotoniczności, na której ta granica się opiera, a która tutaj
nie ma zastosowania -- a jej wrażliwość, łącznie z wrażliwością progu akceptacji z kroku 3 (również domyślną wartością
heurystyczną, ustaloną powyżej na zero), jest oceniana empirycznie, a nie ustalana z założenia (Wyniki). Po czwarte,
niezdominowanie w kroku 4 jest ograniczone do kandydatów wytworzonych w obrębie tej samej iteracji przeszukiwania,
tj.\ wywodzących się od przodków ewaluowanych względem tego samego migawkowego stanu $\mathcal{H}_t$, tak aby
porównywane estymaty $\hat{f}_1$ dzieliły wspólny punkt odniesienia, zamiast być łączone między iteracjami z
potencjalnie dryfującym predyktorem zastępczym.

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
JAHS-Bench-201 \citep{bansal2022jahsbench}, benchmark oparty na predyktorze zastępczym nad wspólną, czternastowymiarową
przestrzenią łączącą kategoryczne wybory architektoniczne z ciągłymi hiperparametrami treningowymi (np.\ współczynnik
uczenia, zanik wag) w trzech zbiorach danych; odpytuje on wyuczony predyktor zastępczy nad ciągłymi wejściami bez
rzeczywistego treningu, więc nie istnieje enumerowalny front oracle (zob.\ Metryki, poniżej). NAS-HPO-Bench-II
\citep{hirose2021nashpobenchii}, stała tablica przeglądowa nad kombinacjami architektury i hiperparametrów, jest
raportowany obok niego jako odpowiednik z Kategorii 1: enumerowalny jest dokładny front oracle, co umożliwia
zastosowanie Inverted Generational Distance plus (IGD+) specyficznie na tym benchmarku. Każdy wynik utrzymujący się na
obu benchmarkach jest raportowany jako główne odkrycie; wynik utrzymujący się tylko na jednym jest raportowany jako
specyficzny dla tego benchmarku i nie jest uogólniany.

**Metody odniesienia.** NSGANetV2 (NSGA-II z bezwzględnym regresorem jako predyktorem zastępczym) jako podstawowa
metoda odniesienia; NSGANetV2 w swoim natywnym, rzeczywistoliczbowym kodowaniu $\Theta$ jako dodatkowa metoda kontrolna
izolująca efekt samej dyskretyzacji, a nie silnika przeszukiwania czy predyktora zastępczego (Kontrole rzetelności);
NSGA-Net (NSGA-II bez predyktora zastępczego, każdy kandydat w pełni ewaluowany) jako ablacja izolująca sam silnik po
stronie NSGA-II, symetryczna do opisanej poniżej ablacji izolującej sam silnik po stronie P3; sam P3, bez żadnego
predyktora zastępczego, jako ablacja izolująca sam silnik po stronie P3; P3 z bezwzględnym regresorem jako predyktorem
zastępczym (w stylu NSGANetV2) jako ablacja izolująca wyłącznie predyktor zastępczy, oddzielająca wkład projektu
świadomego struktury powiązań od wkładu samego silnika P3; przeszukiwanie losowe oraz estymator Parzena o strukturze
drzewiastej (Tree-structured Parzen Estimator, TPE) jako metody odniesienia służące jako test poprawności (sanity
baselines). Ta siatka rozdziela wkłady silnika i predyktora zastępczego na tyle, na ile pozwala na to konstrukcja
eksperymentu, a nie jako pełny ortogonalny plan czynnikowy: relatywny predyktor zastępczy $\hat{\delta}_F$ świadomy
struktury powiązań jest zdefiniowany wyłącznie przy danym drzewie powiązań, więc nie da się skonstruować komórki
NSGA-II-plus-relatywny-predyktor-zastępczy, a wszelką różnicę przypisywaną „predyktorowi zastępczemu” poprzez
porównanie samego P3 z P3Net należy odczytywać z uwzględnieniem tej asymetrii.

Bez predyktora zastępczego, sam P3 stosuje kanoniczną regułę akceptacji optymalnego mieszania: każda proponowana
modyfikacja w obrębie przemiatania jest bramkowana rzeczywistą ewaluacją $f_1$ -- dokładnie tak, jak wyglądałby krok 3
pętli P3Net (Proponowany Optymalizator), gdyby $\hat{\delta}_F$ zastąpić samym $f_1$ -- oraz tak, jak w krokach
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
co P3Net, zamiast swojego zwykłego kodowania rzeczywistoliczbowego, tak aby wszelki zysk był przypisywalny silnikowi
przeszukiwania i predyktorowi zastępczemu, a nie różnicy w rozdzielczości genotypu. Wyrównuje to rozdzielczość, lecz
niekoniecznie jest neutralne: dyskretyzacja usuwa natywne rzeczywistoliczbowe krzyżowanie NSGA-II/NSGANetV2 na
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
NAS-HPO-Bench-II wynoszącej 500 prób przy benchmarkowaniu algorytmów przeszukiwania \citep{hirose2021nashpobenchii}
-- jest to celowy wybór, a nie przeoczenie: pytanie centralne dotyczy budżetu *ograniczonego* (Wprowadzenie), więc
wszystkie trzy poziomy testują reżim ciaśniejszy niż domyślny dla obu benchmarków, na obu benchmarkach jednakowo.
$R = 10$ niezależnych przebiegów na metodę, z ustaloną, opublikowaną listą ziaren losowości, odpowiadającą zalecanemu
minimum JAHS-Bench-201; identyczny schemat inicjalizacji we wszystkich metodach; reguła zatrzymania obejmująca
zarówno budżet ewaluacji, jak i -- jeśli przestrzeń przeszukiwania jest na tyle mała, by przedwcześnie osiągnąć
zbieżność -- kryterium załamania eksploracji analogiczne do tego, które Bartnik musiała dodać dla przestrzeni o skali
NAS-Bench-201 \citep{bartnik2026evolutionary}.

**Metryki.** Hiperwolumen przy ustalonym budżecie oraz, wyłącznie jeśli przestrzeń przeszukiwania dopuszcza
enumerowalny front oracle, IGD+; w przeciwnym razie w jego miejsce stosowany jest hiperwolumen względem najlepszego
znanego frontu. Jakość predyktora zastępczego jest raportowana osobno jako korelacja rangowa (lub dokładność porównań
parowych, jeśli predyktor zastępczy jest relacyjny) między wartościami przewidywanymi a prawdziwymi w funkcji
$|\mathcal{H}_t|$.

**Plan statystyczny.** Zbiór porównań to P3Net przeciwstawiony każdemu z pozostałych siedmiu wariantów (Metody
odniesienia, powyżej), w podziale na benchmark i poziom budżetu -- a nie każda parowa kombinacja spośród wszystkich
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
cache'owania. Wskaźnik ten jest liczony w chwili propozycji -- każdy kandydat wygenerowany przez operator
przeszukiwania, niezależnie od tego, czy zostanie później przechwycony przez pamięć podręczną -- a nie w chwili
ewaluacji, dzięki czemu pozostaje informatywny, mimo że sama pamięć podręczna tłumi ponowną ewaluację wszystkiego, co
liczy. Krzywe zbieżności; postęp frontu Pareto; stabilność między ziarnami losowości.

**Odtwarzalność.** Każda zapisana w pamięci podręcznej ewaluacja jest indeksowana genotypem, typem eksperymentu oraz
ciągiem znaków wersji protokołu obejmującym każde ustawienie wpływające na zarejestrowaną wartość, tak aby zmiana
któregokolwiek z nich automatycznie unieważniała nieaktualne wpisy w pamięci podręcznej, zgodnie ze wzorcem
zastosowanym przez \cite{bartnik2026evolutionary}.

---

## Podsumowanie

- P3Net łączy dwie komplementarne idee: P3 buduje model strukturalnych zależności w genotypie, a predyktor zastępczy eliminuje kosztowne ewaluacje nieobiecujących kandydatów.
- Odpowiedź na pytanie badawcze: czy modelowanie zależności przez P3 przekłada się na lepszą efektywność pętli wspomaganej predyktorem zastępczym w porównaniu z NSGANetV2.
- Ograniczenia: jakość predyktora zastępczego zależy od jakości kodowania genotypu; drzewo rozpinające (MST) zakłada zależności parowe, co może być zbyt grubą aproksymacją dla głęboko ustrukturyzowanych przestrzeni.
- Przyszłe kierunki: silniejszy model predyktora zastępczego (GNN nad grafem komórki), uczenie aktywne do decydowania, których kandydatów poddać pełnej ewaluacji, rozszerzenie na przestrzenie architektur o zmiennej głębokości; trenowanie predyktora zastępczego również na obserwacjach o niższej wierności $f_1^{(k)}$, $k<K$, zamiast wyłącznie na pełnych ewaluacjach przy $r_K$ jak w niniejszej pracy, wykorzystując drabinę wierności wprowadzoną już w sekcji Sformułowanie Problemu -- pominięte tutaj, by utrzymać redukcję kosztu pętli przeszukiwania jako czysto przypisywalną samemu relatywnemu predyktorowi zastępczemu, lecz stanowiące naturalną kolejną dźwignię, gdy ta przypisywalność zostanie już ustalona.

---

## Bibliografia

1. G. Andreadis, T. Alderliesten, P. A. N. Bosman, "Fitness-based Linkage Learning and Maximum-Clique Conditional Linkage Modelling for Gray-Box Optimization with RV-GOMEA," w: *Proceedings of the Genetic and Evolutionary Computation Conference (GECCO)*, 2024.
2. A. Bansal, D. Stoll, M. Janowski, A. Zela, F. Hutter, "JAHS-Bench-201: A Foundation For Research On Joint Architecture And Hyperparameter Search," w: *Advances in Neural Information Processing Systems 35 (NeurIPS 2022), Datasets and Benchmarks Track*, 2022.
3. N. Bartnik, *Evolutionary optimization of deep neural networks*, praca magisterska, Politechnika Wrocławska, Wydział Elektroniki, Fotoniki i Mikrosystemów, promotor: Michał Przewoźniczek, 2026.
4. A. Bouter, P. A. N. Bosman, "A Joint Python/C++ Library for Efficient yet Accessible Black-Box and Gray-Box Optimization with GOMEA," w: *Companion Proceedings of the Genetic and Evolutionary Computation Conference (GECCO Companion)*, 2023.
5. A. Dushatskiy, A. M. Mendrik, T. Alderliesten, P. A. N. Bosman, "Convolutional neural network surrogate-assisted GOMEA," w: *Proceedings of the Genetic and Evolutionary Computation Conference (GECCO)*, 2019, s. 753–761.
6. A. Dushatskiy, T. Alderliesten, P. A. N. Bosman, "A Novel Surrogate-assisted Evolutionary Algorithm Applied to Partition-based Ensemble Learning," w: *Proceedings of the Genetic and Evolutionary Computation Conference (GECCO '21)*, 2021.
7. B. W. Goldman, W. F. Punch, "Parameter-less population pyramid," w: *Proceedings of the 2014 Annual Conference on Genetic and Evolutionary Computation (GECCO)*, 2014, s. 785–792.
8. J. Guerrero-Viu, S. Hauns, S. Izquierdo, G. Miotto, S. Schrodi, A. Biedenkapp, T. Elsken, D. Deng, M. Lindauer, F. Hutter, "Bag of Baselines for Multi-objective Joint Neural Architecture Search and Hyperparameter Optimization," arXiv:2105.01015, 2021.
9. Y. Hirose, N. Yoshinari, S. Shirakawa, "NAS-HPO-Bench-II: A Benchmark Dataset on Joint Optimization of Convolutional Neural Network Architecture and Training Hyperparameters," w: *Proceedings of the Asian Conference on Machine Learning (ACML)*, 2021.
10. Y. Liu, Y. Sun, B. Xue, M. Zhang, G. G. Yen, K. C. Tan, "A survey on evolutionary neural architecture search," *IEEE Transactions on Neural Networks and Learning Systems*, t. 34, nr 2, s. 550–570, 2023.
11. Z. Lu, I. Whalen, V. Boddeti, Y. Dhebar, K. Deb, E. Goodman, W. Banzhaf, "NSGA-Net: neural architecture search using multi-objective genetic algorithm," w: *Proceedings of the Genetic and Evolutionary Computation Conference (GECCO)*, 2019, s. 419–427.
12. Z. Lu, K. Deb, E. Goodman, W. Banzhaf, V. N. Boddeti, "NSGANetV2: Evolutionary Multi-Objective Surrogate-Assisted Neural Architecture Search," w: *Proceedings of the European Conference on Computer Vision (ECCV)*, 2020.
13. Z. Lu, R. Cheng, S. Huang, H. Zhang, C. Qiu, F. Yang, "Surrogate-assisted Multi-objective Neural Architecture Search for Real-time Semantic Segmentation," arXiv:2208.06820, 2022.
14. F. N. Özçelik, M. Ö. Efe, "Evolutionary neural architecture search: a survey," *Turkish Journal of Electrical Engineering and Computer Sciences*, t. 34, nr 4, s. 507–541, 2026.
15. M. W. Przewoźniczek, F. Chicano, M. M. Komarnicki, R. Tinós, "Limited Perfect Monotonical Surrogates Constructed Using Low-Cost Recursive Linkage Discovery with Guaranteed Output," w: *Proceedings of the Genetic and Evolutionary Computation Conference (GECCO)*, 2026, s. 645–653.
16. D. Thierens, P. A. N. Bosman, "Optimal Mixing Evolutionary Algorithms," w: *Proceedings of the 13th Annual Conference on Genetic and Evolutionary Computation (GECCO)*, 2011, s. 617–624.
17. K. H. Tran, L. Truong, A. Vo, N. H. Luong, "Accelerating Gene-pool Optimal Mixing Evolutionary Algorithm for Neural Architecture Search with Synaptic Flow," w: *Companion Proceedings of the Genetic and Evolutionary Computation Conference (GECCO Companion)*, 2023, s. 85–86.
18. C. White, M. Safari, R. Sukthanker, B. Ru, T. Elsken, A. Zela, D. Dey, F. Hutter, "Neural Architecture Search: Insights from 1000 Papers," arXiv:2301.08727, 2023.
19. L. D. Whitley, F. Chicano, B. W. Goldman, "Gray Box Optimization for Mk Landscapes (NK Landscapes and MAX-kSAT)," *Evolutionary Computation*, t. 24, nr 3, s. 491–519, 2016.
20. K. Yu, C. Sciuto, M. Jaggi, C. Musat, M. Salzmann, "Evaluating the Search Phase of Neural Architecture Search," w: *International Conference on Learning Representations (ICLR)*, 2020.
21. A. Zela, A. Klein, S. Falkner, F. Hutter, "Towards Automated Deep Learning: Efficient Joint Neural Architecture and Hyperparameter Search," w: *ICML 2018 AutoML Workshop*, 2018.

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
| Rodowód mechanizmu | Analogiczny do eLyMPuS (empirycznego wariantu LyMPuS, zbudowanego na niekompletnie odkrywanej strukturze zależności) | NAS validation accuracy nie dekomponuje się na podfunkcje (brak dostępu gray-box) — eLyMPuS jest dopasowany do tego reżimu czarnej skrzynki | Prace pokrewne |
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
| Metody odniesienia | NSGANetV2 (główny, zdyskretyzowane $\Theta$); NSGANetV2 w natywnym, ciągłym $\Theta$ (kontrola izolująca efekt samej dyskretyzacji); NSGA-Net bez surogatu, każdy kandydat w pełni ewaluowany (ablacja silnika, strona NSGA-II, symetryczna do wiersza P3 poniżej); P3 bez surogatu (ablacja silnika, strona P3); P3 + regresor bezwzględny w stylu NSGANetV2 (ablacja surogatu); przeszukiwanie losowe i TPE (test poprawności) | Przypisuje zysk do silnika vs. surogatu vs. dyskretyzacji na tyle, na ile pozwala projekt; nie jest to pełna ortogonalna faktoryzacja, bo surogat relatywny $\hat\delta_F$ jest zdefiniowany tylko przy istniejącym drzewie linkage, więc komórka NSGA-II + surogat relatywny nie istnieje | Wyniki |
| Rzeczywistość budżetowa P3-bez-surogatu | Stosuje kanoniczną regułę akceptacji optimal mixing: każdy zaakceptowany krok w sweepie jest bramkowany przez *prawdziwą* ewaluację $f_1$, jak we własnym hill-climbingu/mixowaniu międzypoziomowym P3 | Oczekiwane wyczerpanie większości lub całości budżetu 50–200 w bardzo niewielu sweepach; raportowane wprost (liczba pełnych sweepów ukończonych w budżecie), by słaby wynik czytał się jako głód budżetowy, nie porażka silnika — ten kolaps sam w sobie jest informacyjny, uzasadnia potrzebę surogatu | Wyniki, Metody odniesienia |
| Poziomy budżetu pełnych ewaluacji | Trzy poziomy, $\{50, 100, 200\}$ pełnych ewaluacji, podwajające się na każdym kroku; $R=10$ niezależnych ziaren losowych | Zweryfikowane względem trzech konkretnych liczb z literatury, nie dobrane arbitralnie: (1) własny sugerowany protokół JAHS-Bench-201 to ≈100 ewaluacji, min. 10 ziaren [bansal2022jahsbench] — odpowiada wprost poziomowi środkowemu i $R$; (2) sam NSGANetV2 używa dokładnie 350 pełnych ewaluacji (Tabela 2), by osiągnąć swoje raportowane wyniki [lu2020nsganetv2] — górny poziom (200) pozostaje poniżej tej wartości; (3) własny artykuł NAS-HPO-Bench-II benchmarkuje algorytmy przeszukiwania przy 500 próbach [hirose2021nashpobenchii] — wszystkie trzy poziomy pozostają poniżej i tej wartości, celowo, bo pytanie centralne dotyczy budżetu *ograniczonego* (Wprowadzenie) | Wyniki |
| Metryki | Hiperwolumen przy stałym budżecie zawsze; IGD+ tylko gdy front oracle jest enumerowalny (czyli tylko na NAS-HPO-Bench-II) | Metryka dopasowana do tego, co dany benchmark faktycznie oferuje | Wyniki |
| Plan statystyczny | Sparowany test Wilcoxona + korekcja Holma-Bonferroniego + wielkość efektu (np. delta Cliffa) przy każdej wartości $p$ | Świadomie surowsze niż niekorygowane porównania u Bartnik | Wyniki |
| Zbiór porównań do korekcji | P3Net vs. każde z pozostałych siedmiu ramion, osobno per benchmark i poziom budżetu — nie każda możliwa para wśród wszystkich ramion | Precyzuje, po czym dokładnie liczy się korekcja Holma-Bonferroniego, bo skorygowany próg istotności zależy od tej liczby | Wyniki, Plan statystyczny |
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
| Plan statystyczny: niezdefiniowany „pełny zbiór porównań” | Naprawione | Wyliczone: P3Net vs. każde z pozostałych siedmiu ramion, osobno per benchmark i poziom budżetu | Wyniki, Plan statystyczny |
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
