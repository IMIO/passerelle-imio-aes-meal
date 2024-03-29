# -*- coding: utf-8 -*-


# passerelle-imio-aes-meal - passerelle connector for aes meal management
# Copyright (C) 2016  Entr'ouvert / Imio
#
# This program is free software: you can redistribute it and/or modify it
# under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import ast
import csv
import datetime
import json
import six
import time

from django.db import models
from django.utils.encoding import force_str
from django.utils.translation import ugettext_lazy as _
from passerelle.base.models import BaseResource
from passerelle.utils.api import endpoint


class ImioAesMeal(BaseResource):
    category = _("Datasources manager")
    meal_file = models.FileField(
        _("AES Meal file"),
        upload_to="aes_meal",
        help_text=_("Supported file formats: csv, json"),
    )

    # [fruit,...]
    ignore_types = models.CharField(
        _("Types to ignore"), default="", max_length=128, blank=True
    )
    # An nothing type item can be select.
    nothing = models.BooleanField(
        default=True, verbose_name=_('Authorize to select "nothing" item')
    )
    # , help_text='If "Yes" Use with "one_choice_by_date" set on Additional css class property field')
    # Personal labels
    personal_labels = models.TextField(
        default="{}",
        verbose_name="Personalize labels",
        blank=True,
        help_text='Personal labels: define like a dictionary : {"fruit":"new label fruit","repas":"repas chaud",...}',
    )

    multi_select = models.BooleanField(
        default=True, verbose_name=_("Allows to select multiple items")
    )

    class Meta:
        verbose_name = _("Aes meal importer and serve in wcs")

    datas = {}

    @classmethod
    def get_verbose_name(cls):
        return cls._meta.verbose_name

    @classmethod
    def get_icon_class(cls):
        return ""

    def save(self, *args, **kwargs):
        kwargs.pop("cache", False)
        result = super(ImioAesMeal, self).save(*args, **kwargs)
        return result

    def _detect_dialect_options(self):
        content = self.get_content_without_bom()
        dialect = csv.Sniffer().sniff(content)
        self.dialect_options = {
            k: v for k, v in vars(dialect).items() if not k.startswith("_")
        }

    @property
    def dialect_options(self):
        """Turn dict items into string
        """
        file_type = self.meal_file.name.split(".")[-1]
        if file_type in ("ods", "xls", "xlsx"):
            return None
        # Set dialect_options if None
        if self._dialect_options is None:
            self._detect_dialect_options()
        self.save(cache=False)

        options = {}
        for k, v in self._dialect_options.items():
            if isinstance(v, six.text_type):
                v = force_str(v.encode("ascii"))
            options[force_str(k.encode("ascii"))] = v

        return options

    @dialect_options.setter
    def dialect_options(self, value):
        self._dialect_options = value

    def get_content_without_bom(self):
        """Return the content of the csv as a string

        :return: str
        """
        self.meal_file.seek(0)
        content = self.meal_file.read()
        return force_str(content.decode("utf-8-sig", "ignore").encode("utf-8"))

    def get_rows(self):
        """Return rows, a list of each row from the csvfile

        :return: list
        """
        file_type = self.meal_file.name.split(".")[-1]
        if file_type == "csv":
            content = self.get_content_without_bom()
            self.dialect_options = {'doublequote': False, 'quoting': 0, 'lineterminator': '\r\n',
                                    'skipinitialspace': False, 'quotechar': '"', 'delimiter': '|'}
            reader = csv.reader(content.splitlines(), **self.dialect_options)
            rows = list(reader)
        return rows

    @endpoint(
        perm="can_access",
        methods=["get"],
        description="Retourne Vrai si les dates du CSV sont bien pour le mois prochain",
    )
    def are_meals_up_to_date(self, request, **kwargs):
        """Return True if meals are up to date

        :param request: Any
        :param kwargs: Dict[str, Any]
        :return: bool
        """
        result = False
        # check only on the first date. Maybe stronger if we check on all records?
        first_date_record = self.get_rows()[0][0]
        try:
            date_object = time.strptime(first_date_record, "%d/%m/%Y")
        except Exception:
            return result
        if date_object.tm_year < datetime.date.today().year:
            return result
        if date_object.tm_year > datetime.date.today().year + 1:
            return result
        if date_object.tm_year == datetime.date.today().year:
            if date_object.tm_mon == datetime.date.today().month + 1:
                result = True
        if date_object.tm_year == datetime.date.today().year + 1:
            if date_object.tm_mon == 1 and datetime.date.today().month == 12:
                result = True
        return result

    @endpoint(
        serializer_type="json-api",
        perm="can_access",
        description="Retourne 0 si l'usager a choisi au moins un repas par jour, quand il dispose de la case à cocher "
                    "\"Rien\"",
        parameters={
            "lst_meals": {
                "description": "list of selected meals",
                "example_value": "'_04-11-2019_potage', '_05-11-2019_potage', '_19-11-2019_potage'",
            }
        },
    )
    def zero_if_meals_selected_for_each_day(self, request=None, **kwargs):
        """Return 0 if at least a meal is selected for each day
        if nothing mode is set up

        :param request: request's parameters
        :param kwargs: Dict[str, Any]
        IDs of selected meals
        :return: int
        """
        lst_meals = request.GET["lst_meals"].split(",")
        lst_valid_dates = []
        if self.nothing is True:
            # This is the use-case one choice with "nothing" choice per day.
            all_meals = self.get_rows()
            for m in all_meals:
                if len(m[-1]) == 0:
                    meal_date = m[0]
                    lst_valid_dates.append(meal_date)
            nb_valid_meals = len(set(lst_valid_dates))
            return len(lst_meals) - nb_valid_meals
        else:
            # This is the use-case multi-select checkbox per day.
            return 0

    def has_multi_select(self):
        multi_select = (
            "mult" if self.multi_select is True and self.nothing is False else ""
        )
        return multi_select

    # open and read the file, then listing its content
    def get_data_from_csv(self, menu_file):
        """Transform CSV reader into a list of lists

        :param menu_file: str
        :return: list
        """
        month_menu = [day_menu.split('|') for day_menu in menu_file.split('\n') if len(day_menu) > 1]
        return month_menu

    def set_choice(self, day, meal_category, meal):
        """Set a new choice with a date, meal category and the meal itself

        :param day: str
        date as DD/MM/YYYY
        :param meal_category: str
        :param meal: str
        :return: dict
        """
        # create the id
        item_id = "{}_{}_{}".format(
            "mult" if self.multi_select is True and self.nothing is False else "",
            day.replace("/", "-"),
            meal_category)
        # create the whole item
        result = {"id": item_id,
                  "text": meal,
                  "type": meal_category,
                  }
        # return item
        return result

    def jsonifier(self, csvfile):
        """Transform data from a csv file to use them as a publik's datasource.

        :param csvfile: a csv file formatted like this :
        date as DD/MM/YYYY|soup|meal|fruit|exception (holiday)
        :return: Publik-like json with menu
        """
        jsonified_menu = []
        meal_kind = ("nothing", "potage", "repas", "fruit", "exception")
        for day_menu in self.get_data_from_csv(csvfile):
            # Add a nothing item
            if self.nothing:
                jsonified_menu.append(self.set_choice(day_menu[0], meal_kind[0], 'Rien'))
            # Add other items
            i = 1
            while i < len(day_menu):
                if len(day_menu[i]) > 0 and meal_kind[i] != "exception":
                    jsonified_menu.append(self.set_choice(day_menu[0], meal_kind[i], day_menu[i]))
                i += 1
        return {"data": jsonified_menu}

    @endpoint(
        name="get",
        perm="can_access",
        methods=["get"],
        description="Renvoie le menu CSV sous un format JSON utilisable dans une liste"
    )
    def get(self, request=None, test=None):
        """

        :param request: request's parameters
        :param test: Any
        Useless - but needed because of the wscall configured in WCS
        :return:
        """
        self.datas = self.jsonifier(self.get_content_without_bom())
        return self.datas

    @endpoint(
        name="test",
        perm="can_access",
        methods=["get"],
        description="test : Meals menu is always up to date but it's always the same food.",
    )
    def test_generating_menu(self, request=None):
        """

        :param request: request's parameters
        :return: Dict
        Menu as JSON
        """
        lst_meals = [
            {
                "text": "Potage cresson",
                "type": "potage",
                "id": "{}_03-month-year_potage".format(self.has_multi_select()),
            },
            {
                "text": "Lasagne bolognaise;pur boeuf ",
                "type": "repas",
                "id": "{}_03-month-year_repas".format(self.has_multi_select()),
            },
            {
                "text": "Fruit",
                "type": "fruit",
                "id": "{}_03-month-year_fruit".format(self.has_multi_select()),
            },
            {
                "text": "Potage chou-fleu",
                "type": "potage",
                "id": "{}_04-month-year_potage".format(self.has_multi_select()),
            },
            {
                "text": "Couscous poulet;Bouillon de légumes;Semoule",
                "type": "repas",
                "id": "{}_04-month-year_repas".format(self.has_multi_select()),
            },
            {
                "text": "Yaourt sucré",
                "type": "fruit",
                "id": "{}_04-month-year_fruit".format(self.has_multi_select()),
            },
            {
                "text": "Potage cerfeuil",
                "type": "potage",
                "id": "{}_01-month-year_potage".format(self.has_multi_select()),
            },
            {
                "text": "Carbonnades de boeuf;Carottes;Frites",
                "type": "repas",
                "id": "{}_01-month-year_repas".format(self.has_multi_select()),
            },
            {
                "text": "Fruit",
                "type": "fruit",
                "id": "{}_01-month-year_fruit".format(self.has_multi_select()),
            },
            {
                "text": "Potage champignons",
                "type": "potage",
                "id": "{}_05-month-year_potage".format(self.has_multi_select()),
            },
            {
                "text": "Filet de sole;Haricots verts ",
                "type": "repas",
                "id": "{}_05-month-year_repas".format(self.has_multi_select()),
            },
            {
                "text": "Biscuit",
                "type": "fruit",
                "id": "{}_05-month-year_fruit".format(self.has_multi_select()),
            },
            {
                "text": "Soupe à l'oignon",
                "type": "potage",
                "id": "{}_02-month-year_potage".format(self.has_multi_select()),
            },
            {
                "text": "Pain de veau sce brune;Compote de pommes;Purée",
                "type": "repas",
                "id": "{}_02-month-year_repas".format(self.has_multi_select()),
            },
            {
                "text": "Mimolette",
                "type": "fruit",
                "id": "{}_02-month-year_fruit".format(self.has_multi_select()),
            },
            {
                "text": "Potage julienne",
                "type": "potage",
                "id": "{}_10-month-year_potage".format(self.has_multi_select()),
            },
            {
                "text": "Pilaf aigre doux;(RIZ, lentilles);Salade",
                "type": "repas",
                "id": "{}_10-month-year_repas".format(self.has_multi_select()),
            },
            {
                "text": "Yaourt nature bio & sucrette",
                "type": "fruit",
                "id": "{}_10-month-year_fruit".format(self.has_multi_select()),
            },
            {
                "text": "Potage carotte curry",
                "type": "potage",
                "id": "{}_11-month-year_potage".format(self.has_multi_select()),
            },
            {
                "text": "Salade de pâtes mixtes au jambon (dinde);maïs bio;tomate et petits pois",
                "type": "repas",
                "id": "{}_11-month-year_repas".format(self.has_multi_select()),
            },
            {"text": "Fruit", "type": "fruit", "id": "_11-month-year_fruit"},
            {
                "text": "Potage courgette",
                "type": "potage",
                "id": "{}_12-month-year_potage".format(self.has_multi_select()),
            },
            {
                "text": "Emincé de dinde, jus aux herbes;Brocoli;Pomme de terre",
                "type": "repas",
                "id": "{}_12-month-year_repas".format(self.has_multi_select()),
            },
            {
                "text": "Fruit",
                "type": "fruit",
                "id": "{}_12-month-year_fruit".format(self.has_multi_select()),
            },
            {
                "text": "Potage tomate",
                "type": "potage",
                "id": "{}_08-month-year_potage".format(self.has_multi_select()),
            },
            {
                "text": "Pain hamburger pur boeuf;laitue;Frites",
                "type": "repas",
                "id": "{}_08-month-year_repas".format(self.has_multi_select()),
            },
            {"text": "Pop corn", "type": "fruit", "id": "_08-month-year_fruit"},
            {
                "text": "Potage navet",
                "type": "potage",
                "id": "{}_09-month-year_potage".format(self.has_multi_select()),
            },
            {
                "text": "Filet de saumon sce citron;Epinards à la crème;Purée maison",
                "type": "repas",
                "id": "{}_09-month-year_repas".format(self.has_multi_select()),
            },
            {"text": "Fruit", "type": "fruit", "id": "_09-month-year_fruit"},
            {
                "text": "Potage poireau",
                "type": "potage",
                "id": "{}_18-month-year_potage".format(self.has_multi_select()),
            },
            {
                "text": "Poisson meunière;Ratatouille niçoise;Ebly",
                "type": "repas",
                "id": "{}_18-month-year_repas".format(self.has_multi_select()),
            },
            {
                "text": "Fruit",
                "type": "fruit",
                "id": "{}_18-month-year_fruit".format(self.has_multi_select()),
            },
            {
                "text": "Potage potiron",
                "type": "potage",
                "id": "{}_17-month-year_potage".format(self.has_multi_select()),
            },
            {
                "text": "Emincé de boeuf;Gratin de chou-fleur et de pdt",
                "type": "repas",
                "id": "{}_17-month-year_repas".format(self.has_multi_select()),
            },
            {
                "text": "Biscuit",
                "type": "fruit",
                "id": "{}_17-month-year_fruit".format(self.has_multi_select()),
            },
            {
                "text": "Potage carotte curry",
                "type": "potage",
                "id": "{}_19-month-year_potage".format(self.has_multi_select()),
            },
            {
                "text": "Epigramme d'agneau jus au thym;Flageolets à l'ail;Purée maison",
                "type": "repas",
                "id": "{}_19-month-year_repas".format(self.has_multi_select()),
            },
            {
                "text": "Crème dessert",
                "type": "fruit",
                "id": "{}_19-month-year_fruit".format(self.has_multi_select()),
            },
            {
                "text": "Minestrone",
                "type": "potage",
                "id": "{}_15-month-year_potage".format(self.has_multi_select()),
            },
            {
                "text": "Omelette;Salade vinaigrette;Frites et mayonnaise",
                "type": "repas",
                "id": "{}_15-month-year_repas".format(self.has_multi_select()),
            },
            {
                "text": "Yaourt aux fruits",
                "type": "fruit",
                "id": "{}_15-month-year_fruit".format(self.has_multi_select()),
            },
            {
                "text": "Potage haricots verts",
                "type": "potage",
                "id": "{}_16-month-year_potage".format(self.has_multi_select()),
            },
            {
                "text": "Macaroni;carbonara de dinde aux blancs de poireaux",
                "type": "repas",
                "id": "{}_16-month-year_repas".format(self.has_multi_select()),
            },
            {
                "text": "Fruit",
                "type": "fruit",
                "id": "{}_16-month-year_fruit".format(self.has_multi_select()),
            },
            {
                "text": "Potage tomate boulettes",
                "type": "potage",
                "id": "{}_24-month-year_potage".format(self.has_multi_select()),
            },
            {
                "text": "Sauté de porc aux oignons;Quinoa bio aux petits légumes",
                "type": "repas",
                "id": "{}_24-month-year_repas".format(self.has_multi_select()),
            },
            {
                "text": "Fruit",
                "type": "fruit",
                "id": "{}_24-month-year_fruit".format(self.has_multi_select()),
            },
            {
                "text": "Potage vert pré",
                "type": "potage",
                "id": "{}_25-month-year_potage".format(self.has_multi_select()),
            },
            {
                "text": "Vol-au-vent aux champignons;Purée maison",
                "type": "repas",
                "id": "{}_25-month-year_repas".format(self.has_multi_select()),
            },
            {
                "text": "Biscuit",
                "type": "fruit",
                "id": "{}_25-month-year_fruit".format(self.has_multi_select()),
            },
            {
                "text": "Potage Céleri",
                "type": "potage",
                "id": "{}_26-month-year_potage".format(self.has_multi_select()),
            },
            {
                "text": "Oiseau sans tête;chou-rouge aux pommes;Pomme de terre",
                "type": "repas",
                "id": "{}_26-month-year_repas".format(self.has_multi_select()),
            },
            {
                "text": "Yaourt aromatisé",
                "type": "fruit",
                "id": "{}_26-month-year_fruit".format(self.has_multi_select()),
            },
            {
                "text": "CONGE EXCEPTIONNELLE",
                "type": "exception",
                "id": "{}_22-month-year_exception".format(
                    self.has_multi_select()
                ),
            },
            {
                "text": "Potage brocoli",
                "type": "potage",
                "id": "{}_23-month-year_potage".format(self.has_multi_select()),
            },
            {
                "text": "Dos de lieu;Courgettes à la tomate;Pâtes grecques",
                "type": "repas",
                "id": "{}_23-month-year_repas".format(self.has_multi_select()),
            },
            {
                "text": "Fruit",
                "type": "fruit",
                "id": "{}_23-month-year_fruit".format(self.has_multi_select()),
            },
        ]
        if self.nothing is True:
            current_tmp_date = ""
            lst_tmp = []
            for meal in lst_meals:
                str_tmp_date = meal.get("id").split("_")[1]
                if str_tmp_date != current_tmp_date and meal.get("type") != "exception":
                    lst_tmp.append(
                        {
                            "id": "_{}_{}".format(str_tmp_date, "nothing"),
                            "text": "Rien",
                            "type": "nothing",
                        }
                    )
                current_tmp_date = meal.get("id").split("_")[1]
            lst_meals = lst_meals + lst_tmp
        result = json.loads(
            json.dumps(lst_meals).replace("month", "{:02d}".format(datetime.date.today().month + 1)).replace("year",
                                                                                                             str(
                                                                                                                 datetime.date.today().year))
        )
        return result
