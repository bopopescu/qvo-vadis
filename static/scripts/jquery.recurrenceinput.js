"use strict";

(function ($) {
    $.tools = $.tools || {version: '@VERSION'};

    var tool;
    var LABELS = {};

    tool = $.tools.recurrenceinput = {
        conf: {
            lang: 'en',
            readOnly: false,
            firstDay: 0,

            // "REMOTE" FIELD
            startField: null,
            startFieldYear: null,
            startFieldMonth: null,
            startFieldDay: null,
            ajaxURL: '/recurrenceinput',
            ajaxContentType: 'application/x-www-form-urlencoded',
            ributtonExtraClass: '',

            // INPUT CONFIGURATION
            hasRepeatForeverButton: true,

            // FORM OVERLAY
            formOverlay: {
                speed: 'fast',
                fixed: false
            },

            // JQUERY TEMPLATE NAMES
            template: {
                form: '#jquery-recurrenceinput-form-tmpl',
                display: '#jquery-recurrenceinput-display-tmpl'
            },

            // RECURRENCE TEMPLATES
            rtemplate: {
                daily: {
                    rrule: 'FREQ=DAILY',
                    fields: [
                        'ridailyinterval',
                        'rirangeoptions'
                    ]
                },
                weekly: {
                    rrule: 'FREQ=WEEKLY',
                    fields: [
                        'riweeklyinterval',
                        'riweeklyweekdays',
                        'rirangeoptions'
                    ]
                },
                monthly: {
                    rrule: 'FREQ=MONTHLY',
                    fields: [
                        'rimonthlyinterval',
                        'rimonthlyoptions',
                        'rirangeoptions'
                    ]
                },
                yearly: {
                    rrule: 'FREQ=YEARLY',
                    fields: [
                        'riyearlyinterval',
                        'riyearlyoptions',
                        'rirangeoptions'
                    ]
                }
            }
        },

        localize: function (language, labels) {
            LABELS[language] = labels;
        },

        setTemplates: function (templates, titles) {
            var lang, template;
            tool.conf.rtemplate = templates;
            for (lang in titles) {
                if (titles.hasOwnProperty(lang)) {
                    for (template in titles[lang]) {
                        if (titles[lang].hasOwnProperty(template)) {
                            LABELS[lang].rtemplate[template] = titles[lang][template];
                        }
                    }
                }
            }
        }

    };

    tool.localize("en", {
        displayUnactivate: 'Does not repeat',
        displayActivate: 'Repeats every',
        edit_rules: 'Edit',
        add:  'Add',
        refresh: 'Refresh',

        preview: 'Selected dates',
        addDate: 'Add date',

        recurrenceType: 'Repeats:',

        dailyInterval1: 'Repeat every:',
        dailyInterval2: 'days',

        weeklyInterval1: 'Repeat every:',
        weeklyInterval2: 'week(s)',
        weeklyWeekdays: 'Repeat on:',
        weeklyWeekdaysHuman: 'on:',

        monthlyInterval1: 'Repeat every:',
        monthlyInterval2: 'month(s)',
        monthlyDayOfMonth1: 'Day',
        monthlyDayOfMonth1Human: 'on day',
        monthlyDayOfMonth2: 'of the month',
        monthlyDayOfMonth3: 'month(s)',
        monthlyWeekdayOfMonth1: 'The',
        monthlyWeekdayOfMonth1Human: 'on the',
        monthlyWeekdayOfMonth2: '',
        monthlyWeekdayOfMonth3: 'of the month',
        monthlyRepeatOn: 'Repeat on:',

        yearlyInterval1: 'Repeat every:',
        yearlyInterval2: 'year(s)',
        yearlyDayOfMonth1: 'Every',
        yearlyDayOfMonth1Human: 'on',
        yearlyDayOfMonth2: '',
        yearlyDayOfMonth3: '',
        yearlyWeekdayOfMonth1: 'The',
        yearlyWeekdayOfMonth1Human: 'on the',
        yearlyWeekdayOfMonth2: '',
        yearlyWeekdayOfMonth3: 'of',
        yearlyWeekdayOfMonth4: '',
        yearlyRepeatOn: 'Repeat on:',

        range: 'End recurrence:',
        rangeNoEnd: 'Never',
        rangeByOccurrences1: 'After',
        rangeByOccurrences1Human: 'ends after',
        rangeByOccurrences2: 'occurrence(s)',
        rangeByEndDate: 'On',
        rangeByEndDateHuman: 'ends on',

        including: ', and also',
        except: ', except for',

        cancel: 'Cancel',
        save: 'Save',

        recurrenceStart: 'Start of the recurrence',
        additionalDate: 'Additional date',
        include: 'Include',
        exclude: 'Exclude',
        remove: 'Remove',

        orderIndexes: ['first', 'second', 'third', 'fourth', 'last'],
        months: [
            'January', 'February', 'March', 'April', 'May', 'June',
            'July', 'August', 'September', 'October', 'November', 'December'],
        shortMonths: [
            'Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
            'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'],
        weekdays: [
            'Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday',
            'Friday', 'Saturday'],
        shortWeekdays: [
            'Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'],

        longDateFormat: 'MM d, yy',
        shortDateFormat: 'mm/dd/yy',

        unsupportedFeatures: 'Warning: This event uses recurrence features not ' +
                              'supported by this widget. Saving the recurrence ' +
                              'may change the recurrence in unintended ways:',
        noTemplateMatch: 'No matching recurrence template',
        multipleDayOfMonth: 'This widget does not support multiple days in monthly or yearly recurrence',
        bysetpos: 'BYSETPOS is not supported',
        noRule: 'No RRULE in RRULE data',
        noRepeatEvery: 'Error: The "Repeat every"-field must be between 1 and 1000',
        noEndDate: 'Error: End date is not set. Please set a correct value',
        noRepeatOn: 'Error: "Repeat on"-value must be selected',
        pastEndDate: 'Error: End date cannot be before start date',
        noEndAfterNOccurrences: 'Error: The "After N occurrences"-field must be between 1 and 1000',
        alreadyAdded: 'This date was already added',

        rtemplate: {
            daily: 'Repeats daily',
            weekly: 'Repeats weekly',
            monthly: 'Repeats monthly',
            yearly: 'Repeats yearly'
        }
    });

    tool.localize("es", {
        displayUnactivate: 'Does not repeat',
        displayActivate: 'Repeats every',
        edit_rules: 'Edit',
        add:  'Add',
        refresh: 'Refresh',

        preview: 'Selected dates',
        addDate: 'Add date',

        recurrenceType: 'Repeats:',

        dailyInterval1: 'Repeat every:',
        dailyInterval2: 'days',

        weeklyInterval1: 'Repeat every:',
        weeklyInterval2: 'week(s)',
        weeklyWeekdays: 'Repeat on:',
        weeklyWeekdaysHuman: 'on:',

        monthlyInterval1: 'Repeat every:',
        monthlyInterval2: 'month(s)',
        monthlyDayOfMonth1: 'Day',
        monthlyDayOfMonth1Human: 'on day',
        monthlyDayOfMonth2: 'of the month',
        monthlyDayOfMonth3: 'month(s)',
        monthlyWeekdayOfMonth1: 'The',
        monthlyWeekdayOfMonth1Human: 'on the',
        monthlyWeekdayOfMonth2: '',
        monthlyWeekdayOfMonth3: 'of the month',
        monthlyRepeatOn: 'Repeat on:',

        yearlyInterval1: 'Repeat every:',
        yearlyInterval2: 'year(s)',
        yearlyDayOfMonth1: 'Every',
        yearlyDayOfMonth1Human: 'on',
        yearlyDayOfMonth2: '',
        yearlyDayOfMonth3: '',
        yearlyWeekdayOfMonth1: 'The',
        yearlyWeekdayOfMonth1Human: 'on the',
        yearlyWeekdayOfMonth2: '',
        yearlyWeekdayOfMonth3: 'of',
        yearlyWeekdayOfMonth4: '',
        yearlyRepeatOn: 'Repeat on:',

        range: 'End recurrence:',
        rangeNoEnd: 'Never',
        rangeByOccurrences1: 'After',
        rangeByOccurrences1Human: 'ends after',
        rangeByOccurrences2: 'occurrence(s)',
        rangeByEndDate: 'On',
        rangeByEndDateHuman: 'ends on',

        including: ', and also',
        except: ', except for',

        cancel: 'Cancel',
        save: 'Save',

        recurrenceStart: 'Start of the recurrence',
        additionalDate: 'Additional date',
        include: 'Include',
        exclude: 'Exclude',
        remove: 'Remove',

        orderIndexes: ['first', 'second', 'third', 'fourth', 'last'],
        months: [
            'January', 'February', 'March', 'April', 'May', 'June',
            'July', 'August', 'September', 'October', 'November', 'December'],
        shortMonths: [
            'Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
            'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'],
        weekdays: [
            'Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday',
            'Friday', 'Saturday'],
        shortWeekdays: [
            'Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'],

        longDateFormat: 'MM d, yy',
        shortDateFormat: 'mm/dd/yy',

        unsupportedFeatures: 'Warning: This event uses recurrence features not ' +
            'supported by this widget. Saving the recurrence ' +
            'may change the recurrence in unintended ways:',
        noTemplateMatch: 'No matching recurrence template',
        multipleDayOfMonth: 'This widget does not support multiple days in monthly or yearly recurrence',
        bysetpos: 'BYSETPOS is not supported',
        noRule: 'No RRULE in RRULE data',
        noRepeatEvery: 'Error: The "Repeat every"-field must be between 1 and 1000',
        noEndDate: 'Error: End date is not set. Please set a correct value',
        noRepeatOn: 'Error: "Repeat on"-value must be selected',
        pastEndDate: 'Error: End date cannot be before start date',
        noEndAfterNOccurrences: 'Error: The "After N occurrences"-field must be between 1 and 1000',
        alreadyAdded: 'This date was already added',

        rtemplate: {
            daily: 'Repeats daily',
            weekly: 'Repeats weekly',
            monthly: 'Repeats monthly',
            yearly: 'Repeats yearly'
        }
    });

    tool.localize('nl', {
        displayUnactivate: 'Eenmalig',
        displayActivate: 'elke ',
        edit_rules: 'bewerken',
        add: 'Toevoegen',
        refresh: 'Updaten',
        preview: 'Datums',
        addDate: 'Datum toevoegen',
        recurrenceType: 'elke',
        dailyInterval1: 'om de',
        dailyInterval2: 'dagen',
        weeklyInterval1: 'om de',
        weeklyInterval2: 'weken',
        weeklyWeekdays: 'op',
        weeklyWeekdaysHuman: 'op: ',
        monthlyInterval1: 'om de',
        monthlyInterval2: 'maanden',
        monthlyDayOfMonth1: 'dag',
        monthlyDayOfMonth1Human: 'op dag',
        monthlyDayOfMonth2: 'van de maand',
        monthlyDayOfMonth3: 'maanden',
        monthlyDayOfMonth4: 'monthly_day_of_month_4',
        monthlyWeekdayOfMonth1: 'de',
        monthlyWeekdayOfMonth1Human: 'op de',
        monthlyWeekdayOfMonth2: ' ',
        monthlyWeekdayOfMonth3: 'van de maand',
        monthlyRepeatOn: 'op',
        yearlyInterval1: 'om de',
        yearlyInterval2: 'jaar',
        yearlyDayOfMonth1: '',
        yearlyDayOfMonth1Human: 'op',
        yearlyDayOfMonth2: ' ',
        yearlyDayOfMonth3: ' ',
        yearlyWeekdayOfMonth1: 'de',
        yearlyWeekdayOfMonth1Human: 'op de',
        yearlyWeekdayOfMonth2: ' ',
        yearlyWeekdayOfMonth3: 'van',
        yearlyWeekdayOfMonth4: ' ',
        yearlyRepeatOn: 'op',
        range: 'stopt',
        rangeNoEnd: 'nooit',
        rangeByOccurrences1: 'na',
        rangeByOccurrences1Human: 'stopt na',
        rangeByOccurrences2: 'herhalingen',
        rangeByEndDate: 'op ',
        rangeByEndDateHuman: 'tot ',
        including: ', en ook ',
        except: ', behalve op',
        cancel: 'Annuleren',
        save: 'Gereed',
        recurrenceStart: 'Eerste herhaling',
        additionalDate: 'Extra datums',
        include: 'Inclusief',
        exclude: 'Behalve',
        remove: 'Verwijderen',
        orderIndexes: [
            'eerste', 'tweede', 'derde',
            'vierde', 'laatste'],
        months: [
            'januari', 'februari', 'maart', 'april',
            'mei', 'juni', 'juli', 'augustus',
            'september', 'oktober', 'november', 'december'],
        shortMonths: [
            'jan', 'feb', 'maa',
            'apr', 'mei', 'jun',
            'jul', 'aug', 'sep',
            'okt', 'nov', 'dec'],
        weekdays: [
            'zondag', 'maandag', 'dinsdag', 'woensdag', 'donderdag',
            'vrijdag', 'zaterdag'],
        shortWeekdays: ['zo', 'ma', 'di', 'wo', 'do', 'vr', 'za'],
        longDateFormat: 'DD d MM yy',
        shortDateFormat: 'dd/mm/y',
        unsupportedFeatures: 'Warning: This event uses recurrence features not supported by this widget. Saving the recurrence may change the recurrence in unintended ways: ',
        noTemplateMatch: 'No matching recurrence template',
        multipleDayOfMonth: 'Dieses Widget unterstützt keine mehrfach angelegten Tage in monatlicher oder jährlicher Wiederholung',
        bysetpos: 'BYSETPOS wird nicht unterstützt',
        noRule: 'Keine RRULE in RRULE Daten',
        noRepeatEvery: 'Fout: het veld "om de ..." moet tussen 1 en 1000 liggen',
        noEndDate: 'Fout: de datum om te stoppen is niet ingevuld. Geef een correcte datum in.',
        noRepeatOn: 'Error: "Repeat on"-value must be selected',
        pastEndDate: 'Fout: de datum om te stoppen kan niet voor de startdatum vallen.',
        noEndAfterNOccurrences: 'Fout: het veld "na ... herhalingen" moet tussen 1 en 1000 liggen.',
        alreadyAdded: 'Deze datum is al toegevoegd',
        rtemplate: {
            daily: 'Herhaling elke dag',
            weekly: 'Herhaling elke week',
            monthly: 'Herhaling elke maand',
            yearly: 'Herhaling elk jaar'
        }
    });


    tool.localize('fr', {
        displayUnactivate: 'Événement unique (ne se répète pas)',
        displayActivate: 'Événement régulier. fréquence: (se répète tous les) ',
        edit_rules: 'Editer',
        add: 'Ajouter',
        refresh: 'Rafraîchir',
        preview: 'Sélectionner des dates',
        addDate: 'Ajouter une date',
        recurrenceType: 'Fréquence: (se répète)',
        dailyInterval1: 'Se répète tous les : ',
        dailyInterval2: 'jours',
        weeklyInterval1: 'Se répète tous les : ',
        weeklyInterval2: 'semaine(s)',
        weeklyWeekdays: 'Se répète le:',
        weeklyWeekdaysHuman: 'le (date) ',
        monthlyInterval1: 'Se répète tous les:',
        monthlyInterval2: 'mois',
        monthlyDayOfMonth1: 'Jours',
        monthlyDayOfMonth1Human: 'date:',
        monthlyDayOfMonth2: 'du mois:',
        monthlyDayOfMonth3: 'mois',
        monthlyDayOfMonth4: 'monthly_day_of_month_4',
        monthlyWeekdayOfMonth1: 'Le:',
        monthlyWeekdayOfMonth1Human: 'le:',
        monthlyWeekdayOfMonth2: ' ',
        monthlyWeekdayOfMonth3: 'du mois',
        monthlyRepeatOn: 'Se répète le:',
        yearlyInterval1: 'Se répète tous les',
        yearlyInterval2: 'ans',
        yearlyDayOfMonth1: 'Chaque',
        yearlyDayOfMonth1Human: 'le',
        yearlyDayOfMonth2: ' ',
        yearlyDayOfMonth3: ' ',
        yearlyWeekdayOfMonth1: 'Le',
        yearlyWeekdayOfMonth1Human: 'le',
        yearlyWeekdayOfMonth2: ' ',
        yearlyWeekdayOfMonth3: 'ou',
        yearlyWeekdayOfMonth4: ' ',
        yearlyRepeatOn: 'Se répète le',
        range: 'Fin de la récurrence:',
        rangeNoEnd: 'Jamais',
        rangeByOccurrences1: 'Après',
        rangeByOccurrences1Human: 'fin après:',
        rangeByOccurrences2: 'récurrence:',
        rangeByEndDate: 'Le ',
        rangeByEndDateHuman: 'fin le ',
        including: ', et aussi ',
        except: ', excepté le',
        cancel: 'Annuler',
        save: 'Sauver',
        recurrenceStart: 'Commencer la récurrence',
        additionalDate: 'Date supplémentaire:',
        include: 'Inclus',
        exclude: 'Exclus',
        remove: 'Enlever',
        orderIndexes: [
            'premier', 'second', 'troisième',
            'quatrième', 'dernier'],
        months: [
            'janvier', 'février', 'mars', 'avril',
            'mai', 'juin', 'juillet', 'août',
            'septembre', 'octobre', 'novembre', 'décembre'],
        shortMonths: [
            'jan', 'fév', 'mar',
            'avr', 'mai', 'jun',
            'jul', 'aou', 'sep',
            'oct', 'nov', 'dec'],
        weekdays: [
            'dimanche', 'lundi', 'mardi', 'mercredi', 'jeudi',
            'vendredi', 'samedi'],
        shortWeekdays: ['dim', 'lun', 'mar', 'mer', 'jeu', 'ven', 'sam'],
        longDateFormat: 'DD d MM yy',
        shortDateFormat: 'mm/dd/y',
        unsupportedFeatures: "Attention: cet événement a une occurence qui n'est pas autorisé par ce widget. Sauver cette occurence peut avoir comme effet qu'elle soit modifiée de manière non voulue. ",
        noTemplateMatch: "Il n'y a pas de modèle correspondant à cette occurance.",
        multipleDayOfMonth: "Ce widget n'autorise pas des jours multiples dans l'occurence mensuelle ou annuelle",
        bysetpos: "BYSETPOS n'est pas autorisé",
        noRule: 'Keine RRULE in RRULE Daten',
        noRepeatEvery: "Erreur: le champ 'se répète tous les' doit avoir une valeur comprise entre 1 et 1000",
        noEndDate: "Erreur: la date de fin n'est pas valide. Introduisez une valeur correcte, svp.",
        noRepeatOn: "Erreur: la valeur 'répétée le' doit être sélectionnée",
        pastEndDate: "Erreur: la date finale ne peut être antérieure à la date initiale",
        noEndAfterNOccurrences: "Erreur: le champ 'après N occurences' doit avoir une valeur comprise entre 1 et 1000",
        alreadyAdded: "Cette date a déjà été introduite",
        rtemplate: {
            daily: 'Se répète quotidiennement',
            weekly: 'Se répète hebdomadairement',
            monthly: 'Se répète mensuellement',
            yearly: 'Se répète annuellement'
        }
    });


    var OCCURRENCETMPL = ['<div class="rioccurrences">',
        '{{each occurrences}}',
            '<div class="occurrence ${occurrences[$index].type}">',
                '<span>',
                    '${occurrences[$index].formattedDate}',
                    '{{if occurrences[$index].type === "start"}}',
                        '<span class="rlabel">${i18n.recurrenceStart}</span>',
                    '{{/if}}',
                    '{{if occurrences[$index].type === "rdate"}}',
                        '<span class="rlabel">${i18n.additionalDate}</span>',
                    '{{/if}}',
                '</span>',
                '{{if !readOnly}}',
                    '<span class="action">',
                        '{{if occurrences[$index].type === "rrule"}}',
                            '<a date="${occurrences[$index].date}" href="#"',
                               'class="${occurrences[$index].type}" title="${i18n.exclude}">',
                                '${i18n.exclude}',
                            '</a>',
                        '{{/if}}',
                        '{{if occurrences[$index].type === "rdate"}}',
                            '<a date="${occurrences[$index].date}" href="#"',
                               'class="${occurrences[$index].type}" title="${i18n.remove}" >',
                                '${i18n.remove}',
                            '</a>',
                        '{{/if}}',
                        '{{if occurrences[$index].type === "exdate"}}',
                            '<a date="${occurrences[$index].date}" href="#"',
                               'class="${occurrences[$index].type}" title="${i18n.include}">',
                                '${i18n.include}',
                            '</a>',
                        '{{/if}}',
                    '</span>',
                '{{/if}}',
            '</div>',
        '{{/each}}',
        '<div class="batching">',
            '{{each batch.batches}}',
                '{{if $index === batch.currentBatch}}<span class="current">{{/if}}',
                    '<a href="#" start="${batch.batches[$index][0]}">[${batch.batches[$index][0]} - ${batch.batches[$index][1]}]</a>',
                '{{if $index === batch.currentBatch}}</span>{{/if}}',
            '{{/each}}',
        '</div></div>'].join('\n');

    $.template('occurrenceTmpl', OCCURRENCETMPL);

    var DISPLAYTMPL = ['<div class="ridisplay">',
//        '<div class="rimain">',
//            '{{if !readOnly}}',
//                '<a href="#" name="riedit">${i18n.add_rules}</a>',
//                '<a href="#" name="ridelete" style="display:none">${i18n.delete_rules}</a>',
//            '{{/if}}',
//            '<label class="ridisplay">${i18n.displayUnactivate}</label>',
//        '</div>',
        '<div class="rioccurrences" style="display:none" /></div>'].join('\n');

    $.template('displayTmpl', DISPLAYTMPL);

    var FORMTMPL = [
        '<!-- here begins the recurrence gui -->',
        '<div class="modal riform">',
            '<div id="messagearea" style="display: none;"></div>',
            '<div class="section rirtemplate">',
                '<select class="w-select field" id="rirtemplate" name="rirtemplate">',
                    '{{each rtemplate}}',
                    '<option value="${$index}">${i18n.rtemplate[$index]}</value>',
                    '{{/each}}',
                '</select>',
                '<div>',
                '<div id="riformfields">',
                    '<div id="ridailyinterval" class="rifield">',
                        '<label for="${name}dailyinterval" class="label inline">',
                            '${i18n.dailyInterval1}',
                        '</label>',
                        '<div class="field inline">',
                            '<input class="w-input input-number inline" id="${name}dailyinterval" type="text" value="1" name="ridailyinterval">',
                            '${i18n.dailyInterval2}',
                        '</div>',
                    '</div>',
                    '<div>',
                        '<div id="riweeklyinterval" class="rifield">',
                            '<label for="${name}weeklyinterval" class="label inline">',
                                '${i18n.weeklyInterval1}',
                            '</label>',
                            '<div class="field inline">',
                                '<input class="w-input input-number" id="${name}weeklyinterval" type="text" value="1" name="riweeklyinterval">',
                                '${i18n.weeklyInterval2}',
                            '</div>',
                        '</div>',
                        '<div id="riweeklyweekdays" class="rifield">',
                            '<label for="${name}weeklyinterval" class="label inline">',
                            '${i18n.weeklyWeekdays}',
                            '</label>',
                            '<div class="field">',
                                '{{each orderedWeekdays}}',
                                '<div class="w-checkbox inline margin-right riweeklyweekday">',
                                    '<input class="w-checkbox-input" id="${name}weeklyWeekdays${weekdays[$value]}" type="checkbox" name="riweeklyweekdays${weekdays[$value]}" value="${weekdays[$value]}" {{if $value === 0}}checked{{/if}}>',
                                    '<label class="w-form-label label inline" for="${name}weeklyWeekdays${weekdays[$value]}">',
                                        '${i18n.shortWeekdays[$value]}',
                                    '</label>',
                                '</div>',
                                '{{/each}}',
                            '</div>',
                        '</div>',
                    '</div>',
                    '<div>',
                        '<div id="rimonthlyinterval" class="rifield">',
                            '<label for="${name}monthlyinterval" class="label inline">',
                                '${i18n.monthlyInterval1}',
                            '</label>',
                            '<div class="field inline">',
                                '<input class="w-input input-number inline" type="text" value="1" name="rimonthlyinterval">',
                                '${i18n.monthlyInterval2}',
                            '</div>',
                        '</div>',
                        '<div id="rimonthlyoptions" class="rifield">',
                            '<label for="rimonthlytype" class="label inline">${i18n.monthlyRepeatOn}</label>',
                            '<div>',
                                '<div class="w-radio">',
                                    '<input class="w-radio-input" id="${name}monthlytype:WEEKDAYOFMONTH" type="radio" name="rimonthlytype" value="WEEKDAYOFMONTH" checked>',
                                    '<label class="w-form-label label inline" for="${name}monthlytype:WEEKDAYOFMONTH">',
                                        '${i18n.monthlyWeekdayOfMonth1}',
                                    '</label>',
                                    '<select class="w-select input-text" id="rimonthlyweekdayofmonthindex" name="rimonthlyweekdayofmonthindex">',
                                        '{{each i18n.orderIndexes}}',
                                        '<option value="${orderIndexes[$index]}">${$value}</option>',
                                        '{{/each}}',
                                    '</select>',
                                    '${i18n.monthlyWeekdayOfMonth2}',
                                    '<select class="w-select input-text" id="rimonthlyweekdayofmonth" name="rimonthlyweekdayofmonth">',
                                        '{{each orderedWeekdays}}',
                                        '<option value="${weekdays[$value]}">${i18n.weekdays[$value]}</option>',
                                        '{{/each}}',
                                    '</select>',
                                    '${i18n.monthlyWeekdayOfMonth3}',
                                '</div>',
                            '</div>',
                            '<div class="field">',
                                '<div class="w-radio">',
                                    '<input class="w-radio-input" id="${name}monthlytype:DAYOFMONTH" type="radio" name="rimonthlytype" value="DAYOFMONTH">',
                                    '<label class="w-form-label label inline" for="${name}monthlytype:DAYOFMONTH">',
                                        '${i18n.monthlyDayOfMonth1}',
                                    '</label>',
                                    '<select class="w-select input-number" name="rimonthlydayofmonthday" id="${name}monthlydayofmonthday">',
                                        '{{each [1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31]}}',
                                        '<option value="${$value}">${$value}</option>',
                                        '{{/each}}',
                                    '</select>',
                                    '${i18n.monthlyDayOfMonth2}',
                                '</div>',
                            '</div>',
                        '</div>',
                    '</div>',
                    '<div>',
                        '<div id="riyearlyinterval" class="rifield">',
                            '<label for="monthlyinterval" class="label inline">',
                                '${i18n.yearlyInterval1}',
                            '</label>',
                            '<div class="field inline">',
                                '<input class="w-input input-number inline" type="text" value="1" name="riyearlyinterval">',
                                '${i18n.yearlyInterval2}',
                            '</div>',
                        '</div>',
                        '<div id="riyearlyoptions" class="rifield">',
                            '<label for="riyearlyType" class="label inline">',
                                '${i18n.yearlyRepeatOn}',
                            '</label>',
                            '<div class="field">',
                                '<div>',
                                    '<div class="w-radio">',
                                        '<input class="w-radio-input" id="${name}yearlytype:DAYOFMONTH" type="radio" name="riyearlyType" value="DAYOFMONTH" checked>',
                                        '<label class="w-form-label label inline" for="dayofmonth"></label>',
                                        '<label class="label inline" for="${name}yearlytype:DAYOFMONTH">',
                                            '${i18n.yearlyDayOfMonth1}',
                                        '</label>',
                                        '<select class="w-select input-number" id="riyearlydayofmonthday" name="riyearlydayofmonthday">',
                                            '{{each [1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,',
                                            '18,19,20,21,22,23,24,25,26,27,28,29,30,31]}}',
                                            '<option value="${$value}">${$value}</option>',
                                            '{{/each}}',
                                        '</select>',
                                        '${i18n.yearlyDayOfMonth2}',
                                        '<select class="w-select input-text" id="riyearlydayofmonthmonth" name="riyearlydayofmonthmonth">',
                                            '{{each i18n.months}}',
                                            '<option value="${$index+1}">${$value}</option>',
                                            '{{/each}}',
                                        '</select>',
                                        '${i18n.yearlyDayOfMonth3}',
                                    '</div>',
                                '</div>',
                                '<div>',
                                    '<div class="w-radio">',
                                        '<input class="w-radio-input" id="${name}yearlytype:WEEKDAYOFMONTH" type="radio" name="riyearlyType" value="WEEKDAYOFMONTH">',
                                        '<label class="w-form-label label inline" for="${name}yearlytype:WEEKDAYOFMONTH">',
                                            '${i18n.yearlyWeekdayOfMonth1}',
                                        '</label>',
                                        '<select class="w-select input-text" id="riyearlyweekdayofmonthindex" name="riyearlyweekdayofmonthindex">',
                                            '{{each i18n.orderIndexes}}',
                                            '<option value="${orderIndexes[$index]}">${$value}</option>',
                                            '{{/each}}',
                                        '</select>',
                                        '<label class="label inline" for="${name}yearlytype:WEEKDAYOFMONTH">',
                                            '${i18n.yearlyWeekdayOfMonth2}',
                                        '</label>',
                                        '<select class="w-select input-text" id="riyearlyweekdayofmonthday" name="riyearlyweekdayofmonthday">',
                                            '{{each orderedWeekdays}}',
                                            '<option value="${weekdays[$value]}">${i18n.weekdays[$value]}</option>',
                                            '{{/each}}',
                                        '</select>',
                                        '${i18n.yearlyWeekdayOfMonth3}',
                                        '<select class="w-select input-text" id="riyearlyweekdayofmonthmonth" name="riyearlyweekdayofmonthmonth">',
                                            '{{each i18n.months}}',
                                            '<option value="${$index+1}">${$value}</option>',
                                            '{{/each}}',
                                        '</select>',
                                        '${i18n.yearlyWeekdayOfMonth4}',
                                    '</div>',
                                '</div>',
                            '</div>',
                        '</div>',
                    '</div>',
                    '<div id="rirangeoptions" class="rifield">',
                        '<label class="label">${i18n.range}</label>',
                        '<div class="field">',
                            '{{if hasRepeatForeverButton}}',
                            '<div>',
                                '<div class="w-radio">',
                                    '<input class="w-radio-input" id="${name}rangetype:NOENDDATE" type="radio" name="rirangetype" value="NOENDDATE">',
                                    '<label class="w-form-label label inline" for="${name}rangetype:NOENDDATE">',
                                        '${i18n.rangeNoEnd}',
                                    '</label>',
                                '</div>',
                            '</div>',
                            '{{/if}}',
                            '<div>',
                                '<div class="w-radio">',
                                    '<input class="w-radio-input" id="${name}rangetype:BYOCCURRENCES" type="radio" name="rirangetype" value="BYOCCURRENCES" checked="checked">',
                                    '<label class="w-form-label label inline" for="${name}rangetype:BYOCCURRENCES">',
                                        '${i18n.rangeByOccurrences1}',
                                    '</label>',
                                    '<input class="w-input input-number" id="rirangebyoccurrencesvalue" type="text" name="rirangebyoccurrencesvalue" value="7">',
                                    '<div class="inline">${i18n.rangeByOccurrences2}</div>',
                                '</div>',
                            '</div>',
                            '<div>',
                                '<div class="w-radio">',
                                    '<input class="w-radio-input" id="${name}rangetype:BYENDDATE" type="radio" name="rirangetype" value="BYENDDATE">',
                                    '<label class="w-form-label label inline" for="${name}rangetype:BYENDDATE">',
                                        '${i18n.rangeByEndDate}',
                                    '</label>',
                                    '<input class="w-input input-date date inline" id="rirangebyenddatecalendar" type="text" name="rirangebyenddatecalendar" >',
                                '</div>',
                            '</div>',
                        '</div>',
                    '</div>',  //rirangeoptions
                '</div>',  // riformfields
            '</div>',  //rirtemplate
            '<div class="rioccurrencesactions">',
                '<div class="rioccurancesheader">',
                    '<div>${i18n.preview}</div>',
                '</div>',
            '</div>',  //rioccurrenceactions
            '<div class="rioccurrences"></div>',
            '<div class="rioccurrencesactions">',
                '<div class="rioccurancesheader">',
                    '<div>${i18n.addDate}</div>',
                '</div>',
                '<div class="riaddoccurrence">',
                    '<div class="errorarea"></div>',
                    '<input class="w-input input-date inline date" name="adddate" id="adddate" />',
                    '<a class="button top-button" name="addaction" id="addaction">${i18n.add}</a>',
                '</div>',
            '</div>',  //rioccrrenceactions
            '<div class="ributtons">',
                '<a class="risavebutton ${ributtonExtraClass} button top-button">${i18n.save}</a>',
            '</div>',
        '</div>'  // riform
    ].join('\n');;

    $.template('formTmpl', FORMTMPL);

    // Formatting function (mostly) from jQueryTools dateinput
    var Re = /[dD]{1,2}|[mM]{1,2}|y(?:y)?|"[^"]*"|'[^']*'/g;

    function zeropad(val, len) {
        val = val.toString();
        len = len || 2;
        while (val.length < len) { val = "0" + val; }
        return val;
    }

    function format(date, fmt, conf) {
        var d = date.getDate(),
            D = date.getDay(),
            m = date.getMonth(),
            y = date.getFullYear(),

            flags = {
                d:    d,
                dd:   zeropad(d),
                D:  conf.i18n.shortWeekdays[D],
                DD: conf.i18n.weekdays[D],
                m:    m + 1,
                mm:   zeropad(m + 1),
                M:  conf.i18n.shortMonths[m],
                MM: conf.i18n.months[m],
                y:   String(y).slice(2),
                yy: y
            };

        var result = fmt.replace(Re, function ($0) {
            return flags.hasOwnProperty($0) ? flags[$0] : $0.slice(1, $0.length - 1);
        });

        return result;

    }

    /**
     * Parsing RFC5545 from widget
     */
    function widgetSaveToRfc5545(form, conf, tz) {
        var value = form.find('select[name=rirtemplate]').val();
        var rtemplate = conf.rtemplate[value];
        var result = rtemplate.rrule;
        var human = conf.i18n.rtemplate[value];
        var field, input, weekdays, i18nweekdays, i, j, index, tmp;
        var day, month, year, interval, yearlyType, occurrences, date;

        for (i = 0; i < rtemplate.fields.length; i++) {
            field = form.find('#' + rtemplate.fields[i]);

            switch (field.attr('id')) {

            case 'ridailyinterval':
                interval = field.find('input[name=ridailyinterval]').val();
                if (interval !== '1') {
                    result += ';INTERVAL=' + interval;
                }
                human = interval + ' ' + conf.i18n.dailyInterval2;
                break;

            case 'riweeklyinterval':
                interval = field.find('input[name=riweeklyinterval]').val();
                if (interval !== '1') {
                    result += ';INTERVAL=' + interval;
                }
                human = interval + ' ' + conf.i18n.weeklyInterval2;
                break;

            case 'riweeklyweekdays':
                weekdays = '';
                i18nweekdays = '';
                for (j = 0; j < conf.weekdays.length; j++) {
                    input = field.find('input[name=riweeklyweekdays' + conf.weekdays[j] + ']');
                    if (input.is(':checked')) {
                        if (weekdays) {
                            weekdays += ',';
                            i18nweekdays += ', ';
                        }
                        weekdays += conf.weekdays[j];
                        i18nweekdays += conf.i18n.weekdays[j];
                    }
                }
                if (weekdays) {
                    result += ';BYDAY=' + weekdays;
                    human += ' ' + conf.i18n.weeklyWeekdaysHuman + ' ' + i18nweekdays;
                }
                break;

            case 'rimonthlyinterval':
                interval = field.find('input[name=rimonthlyinterval]').val();
                if (interval !== '1') {
                    result += ';INTERVAL=' + interval;
                }
                human = interval + ' ' + conf.i18n.monthlyInterval2;
                break;

            case 'rimonthlyoptions':
                var monthlyType = $('input[name=rimonthlytype]:checked', form).val();
                switch (monthlyType) {

                case 'DAYOFMONTH':
                    day = $('select[name=rimonthlydayofmonthday]', form).val();
                    result += ';BYMONTHDAY=' + day;
                    human += ', ' + conf.i18n.monthlyDayOfMonth1Human + ' ' + day + ' ' + conf.i18n.monthlyDayOfMonth2;
                    break;
                case 'WEEKDAYOFMONTH':
                    index = $('select[name=rimonthlyweekdayofmonthindex]', form).val();
                    day = $('select[name=rimonthlyweekdayofmonth]', form).val();
                    if ($.inArray(day, ['MO', 'TU', 'WE', 'TH', 'FR', 'SA', 'SU']) > -1) {
                        result += ';BYDAY=' + index + day;
                        human += ', ' + conf.i18n.monthlyWeekdayOfMonth1Human + ' ';
                        human += ' ' + conf.i18n.orderIndexes[$.inArray(index, conf.orderIndexes)];
                        human += ' ' + conf.i18n.monthlyWeekdayOfMonth2;
                        human += ' ' + conf.i18n.weekdays[$.inArray(day, conf.weekdays)];
                        human += ' ' + conf.i18n.monthlyDayOfMonth2;
                    }
                    break;
                }
                break;

            case 'riyearlyinterval':
                interval = field.find('input[name=riyearlyinterval]').val();
                if (interval !== '1') {
                    result += ';INTERVAL=' + interval;
                }
                human = interval + ' ' + conf.i18n.yearlyInterval2;
                break;

            case 'riyearlyoptions':
                yearlyType = $('input[name=riyearlyType]:checked', form).val();
                switch (yearlyType) {

                case 'DAYOFMONTH':
                    month = $('select[name=riyearlydayofmonthmonth]', form).val();
                    day = $('select[name=riyearlydayofmonthday]', form).val();
                    result += ';BYMONTH=' + month;
                    result += ';BYMONTHDAY=' + day;
                    human += ', ' + conf.i18n.yearlyDayOfMonth1Human + ' ' + day + ' ' + conf.i18n.months[month - 1];
                    break;
                case 'WEEKDAYOFMONTH':
                    index = $('select[name=riyearlyweekdayofmonthindex]', form).val();
                    day = $('select[name=riyearlyweekdayofmonthday]', form).val();
                    month = $('select[name=riyearlyweekdayofmonthmonth]', form).val();
                    result += ';BYMONTH=' + month;
                    if ($.inArray(day, ['MO', 'TU', 'WE', 'TH', 'FR', 'SA', 'SU']) > -1) {
                        result += ';BYDAY=' + index + day;
                        human += ', ' + conf.i18n.yearlyWeekdayOfMonth1Human;
                        human += ' ' + conf.i18n.orderIndexes[$.inArray(index, conf.orderIndexes)];
                        human += ' ' + conf.i18n.yearlyWeekdayOfMonth2;
                        human += ' ' + conf.i18n.weekdays[$.inArray(day, conf.weekdays)];
                        human += ' ' + conf.i18n.yearlyWeekdayOfMonth3;
                        human += ' ' + conf.i18n.months[month - 1];
                        human += ' ' + conf.i18n.yearlyWeekdayOfMonth4;
                    }
                    break;
                }
                break;

            case 'rirangeoptions':
                var rangeType = form.find('input[name=rirangetype]:checked').val();
                switch (rangeType) {

                case 'BYOCCURRENCES':
                    occurrences = form.find('input[name=rirangebyoccurrencesvalue]').val();
                    result += ';COUNT=' + occurrences;
                    human += ', ' + conf.i18n.rangeByOccurrences1Human;
                    human += ' ' + occurrences;
                    human += ' ' + conf.i18n.rangeByOccurrences2;
                    break;
                case 'BYENDDATE':
                    field = form.find('input[name=rirangebyenddatecalendar]');
                    var date_js = field.datepicker('getDate');
                    date = $.datepicker.formatDate('yymmdd',date_js);
                    result += ';UNTIL=' + date + 'T000000';
                    if (tz === true) {
                        // Make it UTC:
                        result += 'Z';
                    }
                    human += ', ' + conf.i18n.rangeByEndDateHuman;
                    human += $.datepicker.formatDate( "DD, MM d, yy", date_js, {
                        dayNamesShort: $.datepicker.regional[language].dayNamesShort,
                        dayNames: $.datepicker.regional[language].dayNames,
                        monthNamesShort: $.datepicker.regional[language].monthNamesShort,
                        monthNames: $.datepicker.regional[language].monthNames
                    });
                    break;
                }
                break;
            }
        }

        if (form.ical.RDATE !== undefined && form.ical.RDATE.length > 0) {
            form.ical.RDATE.sort();
            tmp = [];
            for (i = 0; i < form.ical.RDATE.length; i++) {
                if (form.ical.RDATE[i] !== '') {
                    year = parseInt(form.ical.RDATE[i].substring(0, 4), 10);
                    month = parseInt(form.ical.RDATE[i].substring(4, 6), 10) - 1;
                    day = parseInt(form.ical.RDATE[i].substring(6, 8), 10);
                    tmp.push(format(new Date(year, month, day), conf.i18n.longDateFormat, conf));
                }
            }
            if (tmp.length !== 0) {
                human = human + conf.i18n.including + ' ' + tmp.join('; ');
            }
        }

        if (form.ical.EXDATE !== undefined && form.ical.EXDATE.length > 0) {
            form.ical.EXDATE.sort();
            tmp = [];
            for (i = 0; i < form.ical.EXDATE.length; i++) {
                if (form.ical.EXDATE[i] !== '') {
                    year = parseInt(form.ical.EXDATE[i].substring(0, 4), 10);
                    month = parseInt(form.ical.EXDATE[i].substring(4, 6), 10) - 1;
                    day = parseInt(form.ical.EXDATE[i].substring(6, 8), 10);
                    tmp.push(format(new Date(year, month, day), conf.i18n.longDateFormat, conf));
                }
            }
            if (tmp.length !== 0) {
                human = human + conf.i18n.except + ' ' + tmp.join('; ');
            }
        }
        result = 'RRULE:' + result;
        if (form.ical.EXDATE !== undefined && form.ical.EXDATE.join() !== "") {
            tmp = $.map(form.ical.EXDATE, function (x) {
                if (x.length === 8) { // DATE format. Make it DATE-TIME
                    x += 'T000000';
                }
                if (tz === true) {
                    // Make it UTC:
                    x += 'Z';
                }
                return x;
            });
            result = result + '\nEXDATE:' + tmp;
        }
        if (form.ical.RDATE !== undefined && form.ical.RDATE.join() !== "") {
            tmp = $.map(form.ical.RDATE, function (x) {
                if (x.length === 8) { // DATE format. Make it DATE-TIME
                    x += 'T000000';
                }
                if (tz === true) {
                    // Make it UTC:
                    x += 'Z';
                }
                return x;
            });
            result = result + '\nRDATE:' + tmp;
        }
        return {result: result, description: human};
    }

    function parseLine(icalline) {
        var result = {};
        var pos = icalline.indexOf(':');
        var property = icalline.substring(0, pos);
        result.value = icalline.substring(pos + 1);

        if (property.indexOf(';') !== -1) {
            pos = property.indexOf(';');
            result.parameters = property.substring(pos + 1);
            result.property = property.substring(0, pos);
        } else {
            result.parameters = null;
            result.property = property;
        }
        return result;
    }

    function cleanDates(dates) {
        // Get rid of timezones
        // TODO: We could parse dates and range here, maybe?
        var result = [];
        var splitDates = dates.split(',');
        var date;

        for (date in splitDates) {
            if (splitDates.hasOwnProperty(date)) {
                if (splitDates[date].indexOf('Z') !== -1) {
                    result.push(splitDates[date].substring(0, 15));
                } else {
                    result.push(splitDates[date]);
                }
            }
        }
        return result;
    }

    function parseIcal(icaldata) {
        var lines = [];
        var result = {};
        var propAndValue = [];
        var line = null;
        var nextline;

        lines = icaldata.split('\n');
        lines.reverse();
        while (true) {
            if (lines.length > 0) {
                nextline = lines.pop();
                if (nextline.charAt(0) === ' ' || nextline.charAt(0) === '\t') {
                    // Line continuation:
                    line = line + nextline;
                    continue;
                }
            } else {
                nextline = '';
            }

            // New line; the current one is finished, add it to the result.
            if (line !== null) {
                line = parseLine(line);
                 // We ignore properties for now
                if (line.property === 'RDATE' || line.property === 'EXDATE') {
                    result[line.property] = cleanDates(line.value);
                } else {
                    result[line.property] = line.value;
                }
            }

            line = nextline;
            if (line === '') {
                break;
            }
        }
        return result;
    }

    function widgetLoadFromRfc5545(form, conf, icaldata, force) {
        var unsupportedFeatures = [];
        var i, matches, match, matchIndex, rtemplate, d, input, index;
        var selector, selectors, field, radiobutton, start, end;
        var interval, byday, bymonth, bymonthday, count, until;
        var day, month, year, weekday, ical;

        form.ical = parseIcal(icaldata);
        if (form.ical.RRULE === undefined) {
            unsupportedFeatures.push(conf.i18n.noRule);
            if (!force) {
                return -1; // Fail!
            }
        } else {


            matches = /INTERVAL=([0-9]+);?/.exec(form.ical.RRULE);
            if (matches) {
                interval = matches[1];
            } else {
                interval = '1';
            }

            matches = /BYDAY=([^;]+);?/.exec(form.ical.RRULE);
            if (matches) {
                byday = matches[1];
            } else {
                byday = '';
            }

            matches = /BYMONTHDAY=([^;]+);?/.exec(form.ical.RRULE);
            if (matches) {
                bymonthday = matches[1].split(",");
            } else {
                bymonthday = null;
            }

            matches = /BYMONTH=([^;]+);?/.exec(form.ical.RRULE);
            if (matches) {
                bymonth = matches[1].split(",");
            } else {
                bymonth = null;
            }

            matches = /COUNT=([0-9]+);?/.exec(form.ical.RRULE);
            if (matches) {
                count = matches[1];
            } else {
                count = null;
            }

            matches = /UNTIL=([0-9T]+);?/.exec(form.ical.RRULE);
            if (matches) {
                until = matches[1];
            } else {
                until = null;
            }

            matches = /BYSETPOS=([^;]+);?/.exec(form.ical.RRULE);
            if (matches) {
                unsupportedFeatures.push(conf.i18n.bysetpos);
            }

            // Find the best rule:
            match = '';
            matchIndex = null;
            for (i in conf.rtemplate) {
                if (conf.rtemplate.hasOwnProperty(i)) {
                    rtemplate = conf.rtemplate[i];
                    if (form.ical.RRULE.indexOf(rtemplate.rrule) === 0) {
                        if (form.ical.RRULE.length > match.length) {
                            // This is the best match so far
                            match = form.ical.RRULE;
                            matchIndex = i;
                        }
                    }
                }
            }

            if (match) {
                rtemplate = conf.rtemplate[matchIndex];
                // Set the selector:
                selector = form.find('select[name=rirtemplate]').val(matchIndex);
            } else {
                for (rtemplate in conf.rtemplate) {
                    if (conf.rtemplate.hasOwnProperty(rtemplate)) {
                        rtemplate = conf.rtemplate[rtemplate];
                        break;
                    }
                }
                unsupportedFeatures.push(conf.i18n.noTemplateMatch);
            }

            for (i = 0; i < rtemplate.fields.length; i++) {
                field = form.find('#' + rtemplate.fields[i]);
                switch (field.attr('id')) {

                case 'ridailyinterval':
                    field.find('input[name=ridailyinterval]').val(interval);
                    break;

                case 'riweeklyinterval':
                    field.find('input[name=riweeklyinterval]').val(interval);
                    break;

                case 'riweeklyweekdays':
                    byday = byday.split(",");
                    for (d = 0; d < conf.weekdays.length; d++) {
                        day = conf.weekdays[d];
                        input = field.find('input[name=riweeklyweekdays' + day + ']');
                        input.attr('checked', $.inArray(day, byday) !== -1);
                    }
                    break;

                case 'rimonthlyinterval':
                    field.find('input[name=rimonthlyinterval]').val(interval);
                    break;

                case 'rimonthlyoptions':
                    var monthlyType = 'DAYOFMONTH'; // Default to using BYMONTHDAY

                    if (bymonthday) {
                        monthlyType = 'DAYOFMONTH';
                        if (bymonthday.length > 1) {
                            // No support for multiple days in one month
                            unsupportedFeatures.push(conf.i18n.multipleDayOfMonth);
                            // Just keep the first
                            bymonthday = bymonthday[0];
                        }
                        field.find('select[name=rimonthlydayofmonthday]').val(bymonthday);
                    }

                    if (byday) {
                        monthlyType = 'WEEKDAYOFMONTH';

                        if (byday.indexOf(',') !== -1) {
                            // No support for multiple days in one month
                            unsupportedFeatures.push(conf.i18n.multipleDayOfMonth);
                            byday = byday.split(",")[0];
                        }
                        index = byday.slice(0, -2);
                        if (index.charAt(0) !== '+' && index.charAt(0) !== '-') {
                            index = '+' + index;
                        }
                        weekday = byday.slice(-2);
                        field.find('select[name=rimonthlyweekdayofmonthindex]').val(index);
                        field.find('select[name=rimonthlyweekdayofmonth]').val(weekday);
                    }

                    selectors = field.find('input[name=rimonthlytype]');
                    for (index = 0; index < selectors.length; index++) {
                        radiobutton = selectors[index];
                        $(radiobutton).attr('checked', radiobutton.value === monthlyType);
                    }
                    break;

                case 'riyearlyinterval':
                    field.find('input[name=riyearlyinterval]').val(interval);
                    break;

                case 'riyearlyoptions':
                    var yearlyType = 'DAYOFMONTH'; // Default to using BYMONTHDAY

                    if (bymonthday) {
                        yearlyType = 'DAYOFMONTH';
                        if (bymonthday.length > 1) {
                            // No support for multiple days in one month
                            unsupportedFeatures.push(conf.i18n.multipleDayOfMonth);
                            bymonthday = bymonthday[0];
                        }
                        field.find('select[name=riyearlydayofmonthmonth]').val(bymonth);
                        field.find('select[name=riyearlydayofmonthday]').val(bymonthday);
                    }

                    if (byday) {
                        yearlyType = 'WEEKDAYOFMONTH';

                        if (byday.indexOf(',') !== -1) {
                            // No support for multiple days in one month
                            unsupportedFeatures.push(conf.i18n.multipleDayOfMonth);
                            byday = byday.split(",")[0];
                        }
                        index = byday.slice(0, -2);
                        if (index.charAt(0) !== '+' && index.charAt(0) !== '-') {
                            index = '+' + index;
                        }
                        weekday = byday.slice(-2);
                        field.find('select[name=riyearlyweekdayofmonthindex]').val(index);
                        field.find('select[name=riyearlyweekdayofmonthday]').val(weekday);
                        field.find('select[name=riyearlyweekdayofmonthmonth]').val(bymonth);
                    }

                    selectors = field.find('input[name=riyearlyType]');
                    for (index = 0; index < selectors.length; index++) {
                        radiobutton = selectors[index];
                        $(radiobutton).attr('checked', radiobutton.value === yearlyType);
                    }
                    break;

                case 'rirangeoptions':
                    var rangeType = 'NOENDDATE';

                    if (count) {
                        rangeType = 'BYOCCURRENCES';
                        field.find('input[name=rirangebyoccurrencesvalue]').val(count);
                    }

                    if (until) {
                        rangeType = 'BYENDDATE';
                        input = field.find('input[name=rirangebyenddatecalendar]');
                        year = until.slice(0, 4);
                        month = until.slice(4, 6);
                        month = parseInt(month, 10) - 1;
                        day = until.slice(6, 8);
                        input.datepicker('setDate', new Date(year, month, day))
                    }

                    selectors = field.find('input[name=rirangetype]');
                    for (index = 0; index <  selectors.length; index++) {
                        radiobutton = selectors[index];
                        $(radiobutton).attr('checked', radiobutton.value === rangeType);
                    }
                    break;
                }
            }
        }

        var messagearea = form.find('#messagearea');
        if (unsupportedFeatures.length !== 0) {
            messagearea.text(conf.i18n.unsupportedFeatures + ' ' + unsupportedFeatures.join('; '));
            messagearea.show();
            return 1;
        } else {
            messagearea.text('');
            messagearea.hide();
            return 0;
        }

    }

    /**
     * RecurrenceInput - form, display and tools for recurrenceinput widget
     */
    function RecurrenceInput(conf, textarea) {

        var self = this;
        var form, display, body;

        // Extend conf with non-configurable data used by templates.
        var orderedWeekdays = [];
        var index, i;
        for (i = 0; i < 7; i++) {
            index = i + conf.firstDay;
            if (index > 6) {
                index = index - 7;
            }
            orderedWeekdays.push(index);
        }

        $.extend(conf, {
            orderIndexes: ['+1', '+2', '+3', '+4', '-1'],
            weekdays: ['SU', 'MO', 'TU', 'WE', 'TH', 'FR', 'SA'],
            orderedWeekdays: orderedWeekdays
        });

        // The recurrence type dropdown should show certain fields depending
        // on selection:
        function displayFields(selector) {
            var i;
            // First hide all the fields
            form.find('.rifield').hide();
            // Then show the ones that should be shown.
            var value = selector.val();
            if (value) {
                var rtemplate = conf.rtemplate[value];
                for (i = 0; i < rtemplate.fields.length; i++) {
                    form.find('#' + rtemplate.fields[i]).show();
                }
            }
        }

        function occurrenceExclude(event) {
            event.preventDefault();
            if (form.ical.EXDATE === undefined) {
                form.ical.EXDATE = [];
            }
            form.ical.EXDATE.push(this.attributes.date.value);
            var $this = $(this);
            $this.attr('class', 'exdate');
            $this.parent().parent().addClass('exdate');
            $this.unbind(event);
            updateOccurances();
            $this.click(occurrenceInclude); // Jslint warns here, but that's OK.
        }

        function occurrenceInclude(event) {
            event.preventDefault();
            form.ical.EXDATE.splice($.inArray(this.attributes.date.value, form.ical.EXDATE), 1);
            var $this = $(this);
            $this.attr('class', 'rrule');
            $this.parent().parent().removeClass('exdate');
            $this.unbind(event);
            updateOccurances();
            $this.click(occurrenceExclude);
        }

        function occurrenceDelete(event) {
            event.preventDefault();
            form.ical.RDATE.splice($.inArray(this.attributes.date.value, form.ical.RDATE), 1);
            $(this).parent().parent().hide('slow', function () {
                $(this).remove();
            });
        }

        function occurrenceAdd(event) {
            event.preventDefault();
            var field = form.find('.riaddoccurrence input#adddate');
            var date_js = field.datepicker('getDate');
            var datevalue = $.datepicker.formatDate('yymmddT000000',date_js);
            if (form.ical.RDATE === undefined) {
                form.ical.RDATE = [];
            }
            var errorarea = form.find('.riaddoccurrence div.errorarea');
            errorarea.text('');
            errorarea.hide();

            // Add date only if it is not already in RDATE
            if ($.inArray(datevalue, form.ical.RDATE) === -1) {
                form.ical.RDATE.push(datevalue);
                var html = ['<div class="occurrence rdate" style="display: none;">',
                        '<span class="rdate">',
                            $.datepicker.formatDate(conf.i18n.longDateFormat,date_js),
                            '<span class="rlabel">' + conf.i18n.additionalDate + '</span>',
                        '</span>',
                        '<span class="action">',
                            '<a date="' + datevalue + '" href="#" class="rdate" >',
                                'Include',
                            '</a>',
                        '</span>',
                        '</div>'].join('\n');
                form.find('div.rioccurrences').prepend(html);
                $(form.find('div.rioccurrences div')[0]).slideDown();
                $(form.find('div.rioccurrences .action a.rdate')[0]).click(occurrenceDelete);
            } else {
                errorarea.text(conf.i18n.alreadyAdded).show();
            }
        }

        // element is where to find the tag in question. Can be the form
        // or the display widget. Defaults to the form.
        function loadOccurrences(startdate, rfc5545, start, readonly) {
            var element, occurrenceDiv;

            if (!readonly) {
                element = form;
            } else {
                element = display;
            }

            occurrenceDiv = element.find('.rioccurrences');
            occurrenceDiv.hide();

            var year, month, day;
            year = startdate.getFullYear();
            month = startdate.getMonth() + 1;
            day = startdate.getDate();

            var data = {year: year,
                       month: month, // Sending January as 0? I think not.
                       day: day,
                       rrule: rfc5545,
                       format: conf.i18n.longDateFormat,
                       start: start};

            var dict = {
                url: conf.ajaxURL,
                async: false, // Can't be tested if it's asynchronous, annoyingly.
                type: 'post',
                dataType: 'json',
                contentType: conf.ajaxContentType,
                cache: false,
                data: data,
                success: function (data, status, jqXHR) {
                    var result, element;

                    if (!readonly) {
                        element = form;
                    } else {
                        element = display;
                    }
                    data.readOnly = readonly;
                    data.i18n = conf.i18n;

                    // Format dates:
                    var occurrence, date, y, m, d, each;
                    for (each in data.occurrences) {
                        if (data.occurrences.hasOwnProperty(each)) {
                            occurrence = data.occurrences[each];
                            date = occurrence.date;
                            y = parseInt(date.substring(0, 4), 10);
                            m = parseInt(date.substring(4, 6), 10) - 1; // jan=0
                            d = parseInt(date.substring(6, 8), 10);
                            occurrence.formattedDate = format(new Date(y, m, d), conf.i18n.longDateFormat, conf);
                        }
                    }

                    result = $.tmpl('occurrenceTmpl', data);
                    occurrenceDiv = element.find('.rioccurrences');
                    occurrenceDiv.replaceWith(result);

                    // Add the batch actions:
                    element.find('.rioccurrences .batching a').click(
                        function (event) {
                            event.preventDefault();
                            loadOccurrences(startdate, rfc5545, this.attributes.start.value, readonly);
                        }
                    );

                    // Add the delete/undelete actions:
                    if (!readonly) {
                        element.find('.rioccurrences .action a.rrule').click(occurrenceExclude);
                        element.find('.rioccurrences .action a.exdate').click(occurrenceInclude);
                        element.find('.rioccurrences .action a.rdate').click(occurrenceDelete);
                    }
                    // Show the new div
                    //element.find('.rioccurrences').show();
                },
                error: function (jqXHR, textStatus, errorThrown) {
                    alert(textStatus);
                }
            };

            $.ajax(dict);
        }

        function getField(field) {
            // See if it is a field already
            var realField = $(field);
            if (!realField.length) {
                // Otherwise, we assume it's an id:
                realField = $('#' + field);
            }
            return realField;
        }
        function findStartDate() {
            var startdate = null;
            var startField, startFieldYear, startFieldMonth, startFieldDay;

            // Find the default byday and bymonthday from the start date, if any:
            if (conf.startField) {
                startField = getField(conf.startField);
                // Now we have a field, see if it is a dateinput field:
                if (!startField.hasClass('hasDatepicker')) {
                    //No, it wasn't, just try to interpret it with Date()
                    startdate = startField.val();
                    if (startdate === "") {
                        // Probably not an input at all. Try to see if it contains a date
                        startdate = startField.text();
                    }
                } else {
                    // Yes it was, get the date:
                    startdate = startField.datepicker('getDate');
                }
                startdate = new Date(startdate);
            } else if (conf.startFieldYear &&
                       conf.startFieldMonth &&
                       conf.startFieldDay) {
                startFieldYear = getField(conf.startFieldYear);
                startFieldMonth = getField(conf.startFieldMonth);
                startFieldDay = getField(conf.startFieldDay);
                startdate = new Date(startFieldYear.val(),
                                     startFieldMonth.val() - 1,
                                     startFieldDay.val());
            }

            if (startdate === null) {
                return null;
            }
            // We have some sort of startdate:
            if (isNaN(startdate)) {
                return null;
            }
            return startdate;
        }
        function findEndDate(form) {
            var endField, enddate;

            endField = form.find('input[name=rirangebyenddatecalendar]');

            // Now we have a field, see if it is a dateinput field:
            if (!endField.hasClass('hasDatepicker')) {
                //No, it wasn't, just try to interpret it with Date()
                enddate = endField.val();
            } else {
                // Yes it was, get the date:
                enddate = endField.datepicker('getDate');
            }
            enddate = new Date(enddate);

            // if the end date is incorrect or the field is left empty
            if (isNaN(enddate) || endField.val() === "") {
                return null;
            }
            return enddate;
        }
        function findIntField(fieldName, form) {
            var field, num, isInt;

            field = form.find('input[name=' + fieldName + ']');

            num = field.val();

            // if it's not a number or the field is left empty
            if (isNaN(num) || (num.toString().indexOf('.') !== -1) || field.val() === "") {
                return null;
            }
            return num;
        }

        // Loading (populating) display and form widget with
        // passed RFC5545 string (data)
        function loadData(rfc5545) {
            var selector, format, startdate, dayindex, day;

            if (rfc5545) {
                widgetLoadFromRfc5545(form, conf, rfc5545, true);
            }

            startdate = findStartDate();

            if (startdate !== null) {
                // If the date is a real date, set the defaults in the form
                // disabled because the real reference is the RRULE string, not the start date
                /*
                form.find('select[name=rimonthlydayofmonthday]').val(startdate.getDate());
                dayindex = conf.orderIndexes[Math.floor((startdate.getDate() - 1) / 7)];
                day = conf.weekdays[startdate.getDay()];
                form.find('select[name=rimonthlyweekdayofmonthindex]').val(dayindex);
                form.find('select[name=rimonthlyweekdayofmonth]').val(day);
                form.find('select[name=riyearlydayofmonthmonth]').val(startdate.getMonth() + 1);
                form.find('select[name=riyearlydayofmonthday]').val(startdate.getDate());
                form.find('select[name=riyearlyweekdayofmonthindex]').val(dayindex);
                form.find('select[name=riyearlyweekdayofmonthday]').val(day);
                form.find('select[name=riyearlyweekdayofmonthmonth]').val(startdate.getMonth() + 1);
                */

                // Now when we have a start date, we can also do an ajax call to calculate occurrences:
                loadOccurrences(startdate, widgetSaveToRfc5545(form, conf, false).result, 0, false);

                // Show the add and refresh buttons:
                form.find('div.rioccurrencesactions').show();

            } else {
                // No EXDATE/RDATE support
                form.find('div.rioccurrencesactions').hide();
            }


            selector = form.find('select[name=rirtemplate]');
            displayFields(selector);
        }

        function recurrenceOn() {
            var RFC5545 = widgetSaveToRfc5545(form, conf, false);
            var label = body.find('label.ridisplay');
            label.text(conf.i18n.displayActivate + ' ' + RFC5545.description);
            textarea.val(RFC5545.result).change();
            var startdate = findStartDate();
            if (startdate !== null) {
                loadOccurrences(startdate, widgetSaveToRfc5545(form, conf, false).result, 0, true);
            }
            body.find('.riform').show();
            body.find('a[name="riedit"]').text(conf.i18n.edit_rules);
        }

        function recurrenceOff() {
            var label = body.find('label.ridisplay');
            label.text(conf.i18n.displayUnactivate);
            textarea.val('').change();  // Clear the textarea.
            display.find('.rioccurrences').hide();
            body.find('.riform').hide();
            body.find('a[name="riedit"]').text('');
        }

        function checkFields(form) {
            var startDate, endDate, num, messagearea;
            startDate = findStartDate();

            // Hide any error message from before
            messagearea = form.find('#messagearea');
            messagearea.text('');
            messagearea.hide();

            // Hide add field errors
            form.find('.riaddoccurrence div.errorarea').text('').hide();

            // Repeats Daily
            if (form.find('#ridailyinterval').css('display') === 'block') {
                // Check repeat every field
                num = findIntField('ridailyinterval', form);
                if (!num || num < 1 || num > 1000) {
                    messagearea.text(conf.i18n.noRepeatEvery).show();
                    return false;
                }
            }

            // Repeats Weekly
            if (form.find('#riweeklyinterval').css('display') === 'block') {
                // Check repeat every field
                num = findIntField('riweeklyinterval', form);
                if (!num || num < 1 || num > 1000) {
                    messagearea.text(conf.i18n.noRepeatEvery).show();
                    return false;
                }
            }

            // Repeats Monthly
            if (form.find('#rimonthlyinterval').css('display') === 'block') {
                // Check repeat every field
                num = findIntField('rimonthlyinterval', form);
                if (!num || num < 1 || num > 1000) {
                    messagearea.text(conf.i18n.noRepeatEvery).show();
                    return false;
                }

                // Check repeat on
                if (form.find('#rimonthlyoptions input:checked').length === 0) {
                    messagearea.text(conf.i18n.noRepeatOn).show();
                    return false;
                }
            }

            // Repeats Yearly
            if (form.find('#riyearlyinterval').css('display') === 'block') {
                // Check repeat every field
                num = findIntField('riyearlyinterval', form);
                if (!num || num < 1 || num > 1000) {
                    messagearea.text(conf.i18n.noRepeatEvery).show();
                    return false;
                }

                // Check repeat on
                if (form.find('#riyearlyoptions input:checked').length === 0) {
                    messagearea.text(conf.i18n.noRepeatOn).show();
                    return false;
                }
            }

            // End recurrence fields

            // If after N occurences is selected, check its value
            if (form.find('input[value="BYOCCURRENCES"]:visible:checked').length > 0) {
                num = findIntField('rirangebyoccurrencesvalue', form);
                if (!num || num < 1 || num > 1000) {
                    messagearea.text(conf.i18n.noEndAfterNOccurrences).show();
                    return false;
                }
            }

            // If end date is selected, check its value
            if (form.find('input[value="BYENDDATE"]:visible:checked').length > 0) {
                endDate = findEndDate(form);
                if (!endDate) {
                    // if endDate is null that means the field is empty
                    messagearea.text(conf.i18n.noEndDate).show();
                    return false;
                } else if (endDate < startDate) {
                    // the end date cannot be before start date
                    messagearea.text(conf.i18n.pastEndDate).show();
                    return false;
                }
            }

            return true;
        }

        function save(event) {
            event.preventDefault();
            // if no field errors, process the request
            if (checkFields(form)) {
                // close overlay
                body.find('.riform').hide();
                //form.overlay().close();
                //recurrenceOn();
            }
        }

        function cancel(event) {
            event.preventDefault();
            // close overlay
            body.find('.riform').hide();
        }

        function updateOccurances() {
            var startDate;
            startDate = findStartDate();

            // if no field errors, process the request
            if (checkFields(form)) {
                loadOccurrences(startDate,
                    widgetSaveToRfc5545(form, conf, false).result,
                    0,
                    false);
                recurrenceOn();
            }
        }

        /*
          Load the templates
        */

        display = $.tmpl('displayTmpl', conf);
        form = $.tmpl('formTmpl', conf);
        body = $('body');

        // Make an overlay and hide it
        form.ical = {RDATE: [], EXDATE: []};
        form.hide();
        form.find('input[name=rirangebyenddatecalendar]')
            .datepicker('setDate', new Date());

        if (textarea.val()) {
            var result = widgetLoadFromRfc5545(form, conf, textarea.val(), false);
            if (result === -1) {
                var label = body.find('label.ridisplay');
                label.text(conf.i18n.noRule);
            } else {
                recurrenceOn();
            }
        }

        /*
          Do all the GUI stuff:
        */

        // When you check 'Repeating', the recurrence rules should be cleared.
        body.find('input#repeating').change(function(e) {
            if (this.checked) {
                e.preventDefault();
                // Load the form to set up the right fields to show, etc.
                loadData(textarea.val());
                body.find('.riform').show();
                updateOccurances();
            } else {
                e.preventDefault();
                recurrenceOff();
            }
        });

        // Show form overlay when you click on the "Edit..." link
        body.find('a[name=riedit]').click(
            function (e) {
                e.preventDefault();
                // Load the form to set up the right fields to show, etc.
                loadData(textarea.val());
                body.find('.riform').show();
                updateOccurances();
            }
        );

        // Pop up the little add form when clicking "Add"
        form.find('div.riaddoccurrence input#adddate')
            .datepicker('setDate', new Date());
        form.find('a#addaction').click(occurrenceAdd);

        // When the reload button is clicked, reload
//        form.find('a.rirefreshbutton').click(
//            function (event) {
//                event.preventDefault();
//                updateOccurances();
//            }
//        );

        // When selecting template,
        form.find('select[name=rirtemplate]').change(
            function (e) {
                // Update what fieldsets are visible.
                displayFields($(this));
                // Update only if the occurances are shown
                if (form.find('.rioccurrencesactions:visible').length !== 0) {
                    updateOccurances();
                }
            }
        );

        // When focus goes to a drop-down, select the relevant radiobutton.
        form.find('select').change(
            function (e) {
                $(this).parent().find('> input:not(:checked)').click().change();
            }
        );
        form.find('input[name=rirangebyoccurrencesvalue]').change(
            function (e) {
                $(this).parent().find('input[name=rirangetype]:not(:checked)').click().change();
            }
        );
        form.find('input[name=rirangebyenddatecalendar]').change(function () {
            // Update only if the occurances are shown
            $(this).parent().find('input[name=rirangetype]:not(:checked)').click();
            if (form.find('.rioccurrencesactions:visible').length !== 0) {
                updateOccurances();
            }
        });
        // Update the selected dates section
        form.find('#riformfields select, input:radio, .riweeklyweekday > input, input[name=ridailyinterval], input[name=riweeklyinterval], input[name=rimonthlyinterval], input[name=riyearlyinterval], input[name=rirangebyoccurrencesvalue]').change(
            function (e) {
                // Update only if the occurances are shown
                if (form.find('.rioccurrencesactions:visible').length !== 0) {
                    updateOccurances();
                }
            }
        );

        /*
          Save and cancel methods:
        */
        form.find('.ricancelbutton').click(cancel);
        form.find('.risavebutton').click(save);

        /*
         * Public API of RecurrenceInput
         */

        $.extend(self, {
            display: display,
            form: form,
            loadData: loadData, //Used by tests.
            save: save //Used by tests.
        });

    }


    /*
     * jQuery plugin implementation
     */
    $.fn.recurrenceinput = function (conf) {
        if (this.data('recurrenceinput')) {
            // plugin already installed
            return this.data('recurrenceinput');
        }

        // "compile" configuration for widget
        var config = $.extend({}, tool.conf);
        $.extend(config, conf);
        $.extend(config, {i18n: LABELS[config.lang], name: this.attr('name')});

        // our recurrenceinput widget instance
        var recurrenceinput = new RecurrenceInput(config, this);
        // hide textarea and place display widget after textarea
        this.after(recurrenceinput.form);
        //this.after(recurrenceinput.display);

        // hide the textarea
        this.hide();

        // save the data for next call
        this.data('recurrenceinput', recurrenceinput);
        return recurrenceinput;
    };

}(jQuery));
