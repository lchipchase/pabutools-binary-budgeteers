from fractions import Fraction
from mes_swiecie import *
import json
import csv
import math
import sys


################################
####### PARSE PABULIB FILE #####
################################

file = "swiecie2023.pb"  # set this variable
project_id_for_explanation = "23"
short_string_length = 30
max_project_num_dispayed_in_money_spent = 3

e = Election().read_from_files(file).score_to_cost_utilities()

W_first_phase_removed_dict = {c : e.profile[c] for c in e.profile if len(e.profile[c]) / len(e.voters)  * 3 * e.budget < c.cost}
e.profile = {c : e.profile[c] for c in e.profile if c not in W_first_phase_removed_dict}
initial_budget = e.budget

conflicts = {c : set() for c in e.profile}
tie_break = get_tie_break_dict(e)
W_mes, projects_order, money_behind_candidates, budget, res = equal_shares(e, tie_break, conflicts)
W_greedy, _ = utilitarian_greedy(e, tie_break, conflicts)

for c in W_first_phase_removed_dict:
    e.profile[c] = W_first_phase_removed_dict[c]
W_first_phase_removed = [c for c in W_first_phase_removed_dict]

if prefer(e, W_greedy, W_mes):
    print("Zostały wybrane projekty zgodnie z liczbą głosów (metodą większościową).")
    exit(0)

total_cost = sum([c.cost for c in W_mes])
total_points = {}
for c in e.profile:
    total_points[c] = len(e.profile[c])

projects_in_order = [k for k, v in sorted(projects_order.items(), key=lambda item: total_points[item[0]], reverse=True)] + W_first_phase_removed

endowment = budget / len(e.voters)
initial_endowment = initial_budget / len(e.voters)

################################
########## BUILD HTML ##########
################################

template_filename = "template.html"
filename = "explanation.html"

with open(template_filename, "r") as f:
    template = f.read()

for project in e.profile:
    project_id = project.id
    if len(project.name) > 75:
        # Truncate the project name to 80 characters
        truncated_name = project.name[:72] + "..."
        project.name = truncated_name

max_votes = max([len(e.profile[c]) for c in e.profile])
MAX_SUPPORT = endowment * max_votes

def display_int(number):
    return f"{number:,}".replace(",", "&nbsp;")

def display_short_string(name):
    if len(name) <= short_string_length:
        return name
    res = " ".join(name[:short_string_length].split()[:-1])
    return res + "..."

def display_float(number):
    # use comma as decimal separator, \, for thousand separator
    return f"{number:.2f}".replace(".", ",")

def percent(num):
    return f"{80*num/MAX_SUPPORT:.1f}%"

def make_chart(project):
    global template
    global projects_order
    detailed_text_desc1 = ""
    detailed_text_desc2 = ""
    money_behind_candidate = money_behind_candidates[project]
    final_money_behind = money_behind_candidate[0]
    money_lost = []
    for i, candidate in enumerate(W_mes):
        # Rounds are numbered starting with 1.
        if i + 1 > projects_order[project]:
            break
        if len(money_behind_candidate) == i+1:
            break
        paid = money_behind_candidate[i] - money_behind_candidate[i+1]
        money_lost.append((candidate, paid))
        final_money_behind -= paid
    money_lost.reverse()
    html = []
    html.append("<div class='chart-container'>")
    html.append("<div class='cost-locator-container'>")
    tooltip = f"koszt projektu: {display_int(project.cost)} zł" # Text displayed while mouse is over top number
    # Text above the displayed example table row
    detailed_text_desc1 += f"""<h2> Wyjaśnienie diagramu dla przykładowego projektu (Projekt {project.name}) </h2>

                          <p>Koszt projektu {project.name} wynosił {display_int(project.cost)} zł (koszt ten jest oznaczony jako górna strzałka na diagramie). Projekt ten otrzymał {total_points[project]} głosów.
                          Ponieważ na każdego wyborcę przypada {int(endowment)} zł, zwolennikom projektu początkowo przysługuje kwota {display_int(int(money_behind_candidate[0]))} zł
                          (kwota ta jest oznaczona jako dolna strzałka na diagramie).</p>"""
    # Text below the displayed example table row (but before bullet points)
    detailed_text_desc2 += """<p>Kwota początkowo przysługująca tym wyborcom została częściowo przeznaczona na wcześniej wybrane projekty, na które ci wyborcy również zagłosowali: <ul> """
    detailed_text_desc3 = []
    # Div that displays location of project cost on the chart
    html.append(f"<div class='cost-locator' style='left: calc({percent(project.cost)} - 9px);' data-tippy-content='{tooltip}'><b>&darr; {display_int(project.cost)}</b></div>")
    html.append("</div>")

    # Div for the 3-coloured bar.
    html.append("<div class='chart'>")
    # Text shown on mouse-over for blue bar
    if final_money_behind >= project.cost:
        # When product has been funded
        tooltip = f"&#10004; zwolennikom projektu pozostało {display_int(int(final_money_behind))} zł, co wystarcza na pokrycie kosztu {display_int(project.cost)} zł"
        html.append(f"<div class='bar {'bar-blue'}' style='width: {percent(final_money_behind)};' data-tippy-content='{tooltip}'></div>")
    elif money_lost and final_money_behind < project.cost:
        # When project was originally funded but voters no longer have the required funds at this stage of the project
        tooltip = f"&#10008; po sfinansowaniu dotychczasowych projektów, zwolennikom tego projektu pozostało {display_int(int(final_money_behind))} zł, czyli mniej niż {display_int(project.cost)} zł"
        html.append(f"<div class='bar {'bar-blue'}' style='width: {percent(final_money_behind)};' data-tippy-content='{tooltip}'></div>")
    else:
        # Project did not recieve enough votes to be funded at any point in time
        tooltip = f"&#10008; zwolennikom projektu przysługuje jedynie {display_int(int(final_money_behind))} zł, czyli mniej niż {display_int(project.cost)} zł"
        html.append(f"<div class='bar {'bar-blue'}' style='width: {percent(final_money_behind)};' data-tippy-content='{tooltip}'></div>")

    # For red bar
    total_paid = sum([paid for _, paid in money_lost])
    # Sentence above bullet points displayed on red bar mouse-over
    tooltip_data = f"<html lang=\"en\"><body> Z początkowej kwoty wydano <b>{display_int(int(total_paid))} zł</b> na wcześniej wybrane projekty. </br> Najwięcej wydano na: <ul>"
    js_events_highlight = "onmouseover='highlight_project(["
    js_events_unhighlight = " onmouseout='unhighlight_project(["
    displayed_num = 0
    # For each project (list sorted by highest money taken from the row's voters)...
    for candidate, paid in sorted(money_lost, key=lambda item: item[1], reverse=True):
        displayed_num += 1
        # Max 3 projects displayed in tooltip
        if displayed_num <= max_project_num_dispayed_in_money_spent:
            # Adds bullet point to list displayed on red bar mouse-over
            tooltip_data += f" <li>Projekt {candidate.name} ({display_short_string(candidate.id)}): {display_int(int(paid))} zł. <hr style=\"width:{100 * paid/ total_paid}%;height:10px;color:#f6c8c8;background-color:#f6c8c8;text-align:left;margin-left:0\"></hr></li>"
            if displayed_num == 1:
                js_events_highlight += f"\"project-{candidate.name}\""
                js_events_unhighlight += f"\"project-{candidate.name}\""
            else:
                js_events_highlight += f",\"project-{candidate.name}\""
                js_events_unhighlight += f",\"project-{candidate.name}\""
        # Used for displayed example so that it can show ALL projects who have taken money from voters.
        detailed_text_desc3.append(f"<li>Projekt {candidate.name} ({display_short_string(candidate.id)}): wykorzystano na niego {display_int(int(paid))} zł. </li>")
    tooltip_data += "</ul></body></html>"
    js_events_highlight += "])'"
    js_events_unhighlight += "])'"
    # Combines all of the above into one piece of HTML code
    html.append(f"<div class='bar {'bar-light'}' {js_events_highlight} {js_events_unhighlight} style='width: {percent(total_paid)};' data-tippy-content='{tooltip_data}'; allowHTML: true></div>")

    # List of bullet points for example
    for row in detailed_text_desc3:
        detailed_text_desc2 += row

    # Text after bullet points in example
    detailed_text_desc2 += f"""</ul> <p> Całkowita kwota wykorzystana na wcześniej wybrane projekty jest zaznaczona jako różowy pasek na diagramie. Po najechaniu myszką pojawiają się informacje o najbardziej popularnych z tych projektów.</p>
                            <p> Ostatecznie wyborcom pozostało {display_int(int(final_money_behind))} zł. Kwota ta oznaczona jest jako niebieski pasek. Kwota ta jest mniejsza niż koszt projektu, dlatego projekt nie został wybrany."""
    
    # Add explanations for example to template
    if project.name == project_id_for_explanation:
        template = template.replace(
            "!SAMPLE_EXPLANATION1!",
            detailed_text_desc1
        )
        template = template.replace(
            "!SAMPLE_EXPLANATION2!",
            detailed_text_desc2
        )

    html.append("</div>")
    html.append("<div class='cost-locator-container'>")
    inital = int(money_behind_candidate[0])
    tooltip = f"zwolenikom projektu początkowo przysługuje {display_int(inital)} zł"
    html.append(f"<div class='cost-locator' style='left: calc({percent(inital)} - 9px);' data-tippy-content='{tooltip}'><b>&uarr;</b> {display_int(inital)}</div>")
    tooltip = f"zwolenikom projektu pozostało {display_int(int(final_money_behind))} zł"
    # html.append(f"<div class='cost-locator' style='left: calc({percent(final_money_behind)} - 9px);' data-tippy-content='{tooltip}'><b>&uarr;</b></div>")
    # html.append(f"<div class='cost-locator' style='left: calc({percent(final_money_behind)} - 50px);' data-tippy-content='{tooltip}'> {display_int(int(final_money_behind))}</div>")
    html.append("</div>")
    html.append("</div>")
    return "\n".join(html)


CHECKMARK = "&#10004;"

table = []
for project in projects_in_order:
    row = []
    if project in W_mes:
        row.append(f"<tr class='winner' id='project-{project.name}'>")
        row.append(f"<td class='num' style='text-align:right' sorttable_customkey='{projects_order[project]}'> {projects_order[project]} </td>")
        row.append(f"<td class='num' style='text-align:right' sorttable_customkey='{project.name}'>{project.name}</td>")
        row.append(f"<td>{project.id}</td>")
        row.append(f"<td class='num' style='text-align:right' sorttable_customkey='{project.cost}'>{display_int(project.cost)}</td>")
        row.append(f"<td class='num' style='text-align:right' sorttable_customkey='{total_points[project]}'>{display_int(total_points[project])}</td>")
        row.append(f"<td style='text-align:right' sorttable_customkey='{res[project]}'>{res[project]}%</td>")
        row.append(f"<td>{make_chart(project)}</td>")
    elif project not in W_first_phase_removed:
        row.append("<tr class='loser'>")
        row.append(f"<td class='num' style='text-align:right' sorttable_customkey='{len(e.profile) + 1}'>  &#10008; </td>")
        row.append(f"<td class='num' style='text-align:right' sorttable_customkey='{project.name}'>{project.name}</td>")
        row.append(f"<td>{project.id}</td>")
        row.append(f"<td class='num' style='text-align:right' sorttable_customkey='{project.cost}'>{display_int(project.cost)}</td>")
        row.append(f"<td class='num' style='text-align:right' sorttable_customkey='{total_points[project]}'>{display_int(total_points[project])}</td>")
        row.append(f"<td style='text-align:right' sorttable_customkey='{res[project]}'>{res[project]}%</td>")
        row.append(f"<td>{make_chart(project)}</td>")
    else:
        row.append("<tr class='loser-first-phase'>")
        row.append(f"<td class='num' style='text-align:right' sorttable_customkey='{len(e.profile) + 2}'>  &#10008; </td>")
        row.append(f"<td class='num' style='text-align:right' sorttable_customkey='{project.name}'>{project.name}</td>")
        row.append(f"<td>{project.id}</td>")
        row.append(f"<td class='num' style='text-align:right' sorttable_customkey='{project.cost}'>{display_int(project.cost)}</td>")
        row.append(f"<td class='num' style='text-align:right' sorttable_customkey='{total_points[project]}'>{display_int(total_points[project])}</td>")
        row.append(f"<td style='text-align:right' sorttable_customkey='0'></td>")
        row.append("<td>Odrzucony w pierwszej fazie.</td>")
    row.append("</tr>")
    if project.name == project_id_for_explanation:
        template = template.replace(
            "!SAMPLE_EXPLANATION_ROW!",
            "".join(row)
        )
    table += row
template = template.replace(
    "!ROWS!",
    "\n".join(table)
    )

template = template.replace(
    "!FILE!",
    "Wyniki Budżetu Obywatelskiego w Świeciu w 2024"
    )

# Description at top of page
description = f"""<p>W wyborach użyto <a href="https://equalshares.net/pl/">metody równych udziałów</a>. Dostępny budżet wynosił {display_int(initial_budget)} zł, a {display_int(len(e.voters))} mieszkańców oddało poprawny głos. Na każdego głosującego <b>przypadała zatem kwota około {display_int(int(initial_endowment))} zł</b>.
    Ze względu na naturę metody (<a href="https://equalshares.net/pl/implementation/completion">zainteresowanych odsyłamy do szczegółowego opisu</a>) kwota ta wzrosła <b>do {int(endowment)} zł</b>.
    Innymi słowy, każda grupa 100 wyborców mogła zdecydować o projekcie, którego koszt nie przekraczał {display_int(int(endowment * 100))}  zł.
    Spośród zgłoszonych projektów, {display_int(len(e.profile))} zweryfikowano pozytywnie od strony formalnej, z czego <b>{display_int(len(W_mes))} wybrano do realizacji</b>.</p>

    
    <p>Całkowity koszt wybranych projektów wynosi {display_int(total_cost)} zł. Poniżej przedstawiamy listę zgłoszonych projektów. Projekty, które zostały
    wybrane do realizacji zostały oznaczone na zielono. Projekty, które zostały odrzucone w pierwszej fazie oznaczono na czerwono. Są to projekty, które są zbyt drogie w stosunku
    do uzyskanej liczby głosów. (Liczba zwolenników dla takigo projektu podzielona przez liczbę wszystkich głosujących jest mniejsza niż koszt projektu podzielony przez trzykrotną wartość dostępnego budżetu.) </p>
     
    <p>Przy każdym projekcie podajemy jego koszt i liczbę głosów, które otrzymał. Ponadto, dla każdego projektu podajemy jego <b>efektywne poparcie</b>,
    które jest procentową wartością opisującą w jakim stopniu wielkość poparcia przekracza próg wymagany do akceptacji projektu:
    wartość powyżej 100% oznacza, że projekt został wybrany, a wartość poniżej 100% oznacza, że projekt nie został wybrany.
    Przykładowo, wartość efektywnego poparcia na poziomie 60% oznacza, że projekt otrzymał 60% głosów wymaganych do akceptacji. </p>

    Projekty mogły zostać niewybrane z jednego z następujących powodów:
    <ol>
    <li>projekt otrzymał zbyt mało głosów w stosunku do swojego kosztu, lub </li>
    <li>wyborcy, którzy głosowali na dany projekt głosowali również na inne bardziej popularne projekty, zatem ich głosy przełożyły się w pierwszej kolejności na sfinansowanie tych bardziej popularnych projektów. </li>
    </ol>
    
    <p>Przy każdym projekcie przedstawiamy również <b>diagram słupkowy</b>. Wyjaśnia on jaką kwotą zwolennicy każdego projektu początkowo dysponowali.
    Na diagramach możemy również zobaczyć, dlaczego dany projekt nie został wybrany. W szzcególności, możemy zobaczyć na które bardziej popularne projekty głosowali
    zwolennicy danego niewybranego projektu, oraz jaka część przysługujących im środków została przeznaczona na te bardziej popularne projekty. </p>
    """

template = template.replace(
    "!DESCRIPTION!",
    description
    )
    

comparison = f"""<p>  
    <ol>
    <li>W przypadku metody równych udziałów {display_float(excl_ratio(e, W_mes))}% wyborców nie otrzymało żadnego z projektów, na który zagłosowali. Gdyby użyć metody większościowej, to odsetek ten wynosiłby {display_float(excl_ratio(e, W_greedy))}%. </li>
    <li>W przypadku metody równych udziałów średnio dla wyborcy wybrano {display_float(avg_util(e, W_mes))} projektów spośród tych na które zagłosował. Gdyby użyć metody większościowej, to liczba ta wynosiłaby {display_float(avg_util(e, W_greedy))}.</li>
    </ol>
    """

template = template.replace(
    "!COMPARISON!",
    comparison
    )    


with open(filename, "w", encoding="utf-8") as f:
    f.write(template)