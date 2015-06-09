from gnue.common.formatting import GTypecast
from gnue.forms import GFObjects, GFLibrary, GFForm
from gnue.forms.GFObjects import commanders

		
    xmlElements = {
        'form' : {
            'BaseClass' : GFForm.GFForm,
            'Required' : True,
            'SingleInstance' : True,
            'Label' : u_('Form'),
            'Attributes' : {
                'title' : {
                    'Typecast' : GTypecast.text,
                    'Default' : 'Untitled Form',
                    'Label' : _('Title'),
                    'Description' : 'The title of the form.'},
                'readonly' : {
                    'Typecast' : GTypecast.boolean,
                    'Default' : False,
                    'Label' : _('Read Only'),
                    'Description' : 'If set to {Y}, then no modifications to data '
                                    'by the end user will be allowed. The form will '
                                    'become a query-only form.'},
                'name' : {
                    'Unique' : True,
                    'Typecast' : GTypecast.name,
                    'Label' : _('Name'),
                    'Description' : 'A unique name or ID for the form.'},
                'style' : {
                    'Typecast' : GTypecast.name,
                    'Label' : _('Style'),
                    'ValueSet' : {
                        'normal' : {
                            'Label' : _('Normal')},
                        'dialog' : {
                            'Label' : _('Dialog')}},
                    'Default' : 'normal',
                    'Description' : 'Display as normal or dialog-style window.'},
            },
            'ParentTags' : None,
            'Description' : 'Top-level element that encloses all the logic '
                            'and visuals that the user interface will show '
                            'to the user.'},
        'menu' : {
            'Description' : u_("A menu or submenu containing menu items and/or submenus"),
            'BaseClass' : commanders.GFMenu,
            'ParentTags' : ('form', 'dialog', 'menu'),
            'Label' : u_('Menu'),
            'Attributes' : {
                'name' : {
                    'Label' : u_("Name"),
                    'Description' : u_("Name of this element"),
                    'Typecast' : GTypecast.name,
                    'Required' : True,
                    'Unique' : True},
                'label' : {
                    'Label' : u_("Label"),
                    'Description' : u_("Text to use if this is a submenu"),
                    'Typecast' : GTypecast.text}}},
        'menuitem' : {
            'Description' : u_("A menu item that fires a trigger when selected"),
            'BaseClass' : commanders.GFMenuItem,
            'Label' : u_('Menu Item'),
            'ParentTags' : ['menu'],
            'Attributes' : {
                'name' : {
                    'Label' : u_("Name"),
                    'Description' : u_("Name of this element"),
                    'Typecast' : GTypecast.name,
                    'Required' : True,
                    'Unique' : True},
                'icon' : {
                    'Label' : u_("Icon"),
                    'Description' : u_("Icon to display besides this menu item"),
                    'Typecast' : GTypecast.name},
                'label' : {
                    'Label' : u_("Label"),
                    'Description' : u_("Text to use for this menu item"),
                    'Typecast' : GTypecast.text},
                'description' : {
                    'Label' : u_("Description"),
                    'Description' : u_("Text to display in the status bar for this menu "
                                       "item"),
                    'Typecast' : GTypecast.text},
                'action' : {
                    'Label' : u_("Action"),
                    'Description' : u_("Name of the trigger to run whenever this menu "
                                       "item is selected"),
                    'Typecast' : GTypecast.name,
                    'References' : 'trigger.name'},
                'action_off' : {
                    'Label' : u_("Action Off"),
                    'Description' : u_("Name of the trigger to run whenever this menu "
                                       "item is switched to off"),
                    'Typecast' : GTypecast.name,
                    'References' : 'trigger.name'},
                'hotkey' : {
                    'Label' : u_("Hotkey"),
                    'Description' : u_("Hotkey to assign to this menu item"),
                    'Typecast' : GTypecast.text},
                'state' : {
                    'Label' : u_("State"),
                    'Description' : u_("Determines whether this menu item will be "
                                       "switched on by default"),
                    'Typecast' : GTypecast.boolean,
                    'Default' : False},
                'enabled' : {
                    'Label' : u_("Enabled"),
                    'Description' : u_("Determines whether this menu item will be "
                                       "enabled by default"),
                    'Typecast' : GTypecast.boolean,
                    'Default' : True}}},
        'toolbar' : {
            'Description' : u_("A toolbar containing tool buttons"),
            'BaseClass' : commanders.GFToolbar,
            'ParentTags' : ('form', 'dialog'),
            'Label' : u_('Toolbar'),
            'Attributes' : {
                'name' : {
                    'Label' : u_("Name"),
                    'Description' : u_("Name of this element"),
                    'Typecast' : GTypecast.name,
                    'Required' : True,
                    'Unique' : True}}},
        'toolbutton' : {
            'Description' : u_("A button on a toolbar"),
            'BaseClass' : commanders.GFToolButton,
            'ParentTags' : ['toolbar'],
            'Label' : u_('Toolbar Button'),
            'Attributes' : {
                'name' : {
                    'Label' : u_("Name"),
                    'Description' : u_("Name of this element"),
                    'Typecast' : GTypecast.name,
                    'Required' : True,
                    'Unique' : True},
                'icon' : {
                    'Label' : u_("Icon"),
                    'Description' : u_("Icon to display on the button"),
                    'Typecast' : GTypecast.name},
                'label' : {
                    'Label' : u_("Label"),
                    'Description' : u_("Text to display on the button"),
                    'Typecast' : GTypecast.text},
                'description' : {
                    'Label' : u_("Description"),
                    'Description' : u_("Text to display in a tooltip window"),
                    'Typecast' : GTypecast.text},
                'action' : {
                    'Label' : u_("Action"),
                    'Description' : u_("Name of the trigger to run whenever this button "
                                       "is clicked"),
                    'Typecast' : GTypecast.name,
                    'References' : 'trigger.name'},
                'action_off' : {
                    'Label' : u_("Action Off"),
                    'Description' : u_("Name of the trigger to run whenever this button "
                                       "is switched to off"),
                    'Typecast' : GTypecast.name,
                    'References' : 'trigger.name'},
                'state' : {
                    'Label' : u_("State"),
                    'Description' : u_("Determines whether this button will be switched "
                                       "on by default"),
                    'Typecast' : GTypecast.boolean,
                    'Default' : False},
                'enabled' : {
                    'Label' : u_("Enabled"),
                    'Description' : u_("Determines whether this button will be enabled "
                                       "by default"),
                    'Typecast' : GTypecast.boolean,
                    'Default' : True}}},
        'logic' : {
            'BaseClass' : GFObjects.GFLogic,
            'Importable' : True,
            'SingleInstance' : True,
            'ParentTags' : ('form', 'dialog'),
            'Label' : u_('Logic'),
            'Description' : 'Separation layer that contains "Business logic": '
                            'blocks, fields, block-level and field-level triggers.'},
        'layout' : {
            'BaseClass' : GFObjects.GFLayout,
            'Importable' : True,
            'SingleInstance' : True,
            'ParentTags' : ('form', 'dialog'),
            'Label' : u_('Layout'),
            'Description' : 'Separation layer that contains all the '
                            'visual elements on the form.',
            'Attributes' : {
                'tabbed' : {
                    'Typecast' : GTypecast.name,
                    'Label' : _('Tab Location'),
                    'ValueSet' : {
                        'none' : {
                            'Label' : _('No tabs')},
                        'left' : {
                            'Label' : _('Left tabs')},
                        'right' : {
                            'Label' : _('Right tabs')},
                        'bottom' : {
                            'Label' : _('Botton tabs')},
                        'top' : {
                            'Label' : _('Top tabs')}},
                    'Default' : "none",
                    'Description' : 'Informs the UI subsystem to display a form\'s pages '
                                    'as notebook tabs. Allowed values are {left}, '
                                    '{right}, {bottom}, {top}.  If the UI driver in use '
                                    'does not support the chosen tab position '
                                    '(or tabs at all,) then the UI driver may choose '
                                    'another tab position.'},
                'name' : {
                    'Unique' : True,
                    'Typecast' : GTypecast.name,
                    'Label' : _('Name'),
                    'Default' : 'layout',
                    'Description' : 'A unique name or ID for the form.'},
            }},

        'page' : {
            'BaseClass' : GFObjects.GFPage,
            'Importable' : True,
            'Attributes' : {
                'name' : {
                    'Unique' : True,
                    'Typecast' : GTypecast.name,
                    'Description' : 'A unique ID for the widget. This is only useful '
                                    'when importing pages from a library.'},
                'transparent' : {
                    'Typecast' : GTypecast.boolean,
                    'Default' : False,
                    'Description' : 'If set, then you can tab out of the page via next- '
                                    'or previous-field events. Makes navigation in '
                                    'mutlipage forms easier. If false, focus stays '
                                    'within a page until user explicitly moves to '
                                    'another page'},
                'style' : {
                    'Typecast' : GTypecast.name,
                    'ValueSet' : {
                        'normal' : {
                            'Label' : _('Normal')},
                        ## TODO ##         'popup': {},
                    },
                    'Default' : 'normal',
                    'Description' : 'The type of page.'},
                'caption' : {
                    'Typecast' : GTypecast.text,
                    'Description' : 'For {tabbed} or {popup} pages, this contains '
                                    'the caption to use for the page.'}},

            'ParentTags' : ('layout', ),
            'Label' : u_('Page'),
            'Description' : 'Encapsulates visual elements to be displayed '
                            'on a page.'},
        'block' : {
            'BaseClass' : GFObjects.GFBlock,
            'Importable' : True,
            'Attributes' : {
                'name' : {
                    'Required' : True,
                    'Unique' : True,
                    'Typecast' : GTypecast.name,
                    'Description' : 'A unique ID (name) for the widget. '
                                    'No blocks can share '
                                    'the same name without causing namespace '
                                    'collisions in user triggers.'},
                'rows' : {
                    'Typecast' : GTypecast.whole,
                    'Description' : 'Any widgets inside the block will display this '
                                    'number of copies in a verticle column. Simulates '
                                    'a grid entry system.'},
                'rowSpacer' : {
                    'Typecast' : GTypecast.whole,
                    'Label' : _('Row Spacing'),
                    'Description' : 'Adjusts the vertical gap of this number of rows '
                                    'between duplicated widgets. Serves the same '
                                    'purpose as some of the gap attributes on '
                                    'individual widgets.'},
                'startup' : {
                    'Label' : u_("Startup state"),
                    'Description' : u_("State in which the block will be on form startup. "
                                       "'Empty' means the block is filled with a single empty "
                                       "record, 'full' means the block is populated with the "
                                       "result of a full query."),
                    'Typecast' : GTypecast.name,
                    'ValueSet' : {
                        'empty' : {
                            'Label' : u_('Empty')},
                        'full' : {
                            'Label' : u_('Full')}},
                    'Default' : 'empty'},
                'transparent' : {
                    'Typecast' : GTypecast.boolean,
                    'Label' : _('Transparent Nav'),
                    'Default' : True,
                    'Description' : 'If set, then you can tab out of the block via next- '
                                    'or previous-field events. Makes navigation in '
                                    'multiblock forms easier. If false, focus stays '
                                    'within a block until user explicitly moves to '
                                    'another block. Note that a block\'s {autoNextRecord}'
                                    'setting affects {transparent} behavior'},
                'autoCreate' : {
                    'Typecast' : GTypecast.boolean,
                    'Label' : _('Auto Create Record'),
                    'Default' : True,
                    'Description' : 'If set, then if you attempt to go to the next record '
                                    'while at the last record, a new record is created.'},
                'autoNextRecord' : {
                    'Typecast' : GTypecast.boolean,
                    'Label' : _('Auto Next Record'),
                    'Default' : False,
                    'Description' : 'If set, then if you tab at the end of a block, you '
                                    'will be taken to the next record. If the current '
                                    'record is empty and transparent is true, then '
                                    'you will be taken to the next block'},
                'autoCommit' : {
                    'Typecast' : GTypecast.boolean,
                    'Label' : _('Auto Commit'),
                    'Default' : False,
                    'Description' : 'If set, then the datasource will automatically '
                                    'commit changes when trying to navigate out of the '
                                    'current record.'},
                'autoClear' : {
                    'Typecast' : GTypecast.boolean,
                    'Label' : _('Auto Clear on Commit'),
                    'Default' : False,
                    'Description' : 'If set, then the block is cleared/emptied on '
                                    'a commit.'},
                'editable' : {
                    'Description' : 'Can records be edited/created?',
                    'Label' : _('Allow Editing'),
                    'ValueSet' : {
                        'Y' : {
                            'Label' : _('Yes')},
                        'N' : {
                            'Label' : _('No')},
                        'update' : {
                            'Label' : _('Update Only')},
                        'new' : {
                            'Label' : _('New Records Only')}},
                    'Typecast' : GTypecast.text,
                    'Default' : 'Y'},
                'queryable' : {
                    'Description' : 'Can records be queried?',
                    'Label' : _('Allow Querying'),
                    'Typecast' : GTypecast.boolean,
                    'Default' : True},
                'deletable' : {
                    'Description' : 'Can records be deleted?',
                    'Label' : _('Allow Deletes'),
                    'Typecast' : GTypecast.boolean,
                    'Default' : True},
                'navigable' : {
                    'Description' : 'Can this block be navigated?',
                    'Label' : _('Navigable'),
                    'Typecast' : GTypecast.boolean,
                    'Default' : True},
                'restrictDelete' : {
                    'Typecast' : GTypecast.boolean,
                    'Default' : False,
                    'Deprecated' : 'Use deletable="N"',
                    'Label' : _('Prevent Deletes'),
                    'Description' : 'If set then the user will be unable to request '
                                    'that a record be deleted via the user interface.'},
                'restrictInsert' : {
                    'Typecast' : GTypecast.boolean,
                    'Default' : False,
                    'Label' : _('Prevent Inserts'),
                    'Deprecated' : 'Use editable="update"',
                    'Description' : 'If set then the user will be unable to request '
                                    'that new records be inserted into the block.'},
                'datasource' : {
                    'References' : 'datasource.name',
                    'Typecast' : GTypecast.name,
                    'Description' : 'The name of a datasource (defined in by a '
                                    '{<datasource>} tag) that provides this block '
                                    'with it\'s data.'}},

            'ParentTags' : ('logic', ),
            'Label' : u_('Block'),
            'Description' : 'A block contains instructions on how Forms '
                            'should interact with a datasource.'},
        'label' : {
            'BaseClass' : GFObjects.GFLabel,
            'Attributes' : {
                'name' : {
                    'Unique' : True,
                    'Typecast' : GTypecast.name,
                    'Description' : u_('The unique ID of the label.')},
                'text' : {
                    'Required' : True,
                    'Typecast' : GTypecast.text,
                    'Description' : u_('The text to be displayed.')},
                'for' : {
                    'Required' : False,
                    'References' : 'entry.name',
                    'Typecast' : GTypecast.name,
                    'Description' : u_('If this label is for a specific object, '
                                       'name it here.')},
                'alignment' : {
                    'Typecast' : GTypecast.name,
                    'ValueSet' : {
                        'left' : {
                            'Label' : u_('Left')},
                        'right' : {
                            'Label' : u_('Right')},
                        'center' : {
                            'Label' : u_('Centered')}},
                    'Default' : "left",
                    'Description' : 'The justification of the label. Can be one of '
                                    'the following: {left}, {right}, or {center}. '
                                    'Requires that the {width} attribute be set.'},
                'rows' : {
                    'Typecast' : GTypecast.whole,
                    'Description' : 'Overrides the rows setting defined at the '
                                    'block level. '},
                'rowSpacer' : {
                    'Typecast' : GTypecast.whole,
                    'Label' : _('Row Spacing'),
                    'Description' : 'Overriders the rowSpace setting defined at the '
                                    'block level.'}},

            'Positionable' : True,
            'ParentTags' : ('page', 'box', 'hbox', 'vbox'),
            'Label' : u_('Label'),
            'Description' : 'Displays static text'},
        'field' : {
            'BaseClass' : GFObjects.GFField,
            'Importable' : True,
            'Attributes' : {
                'name' : {
                    'Required' : True,
                    'Unique' : True,
                    'Typecast' : GTypecast.name,
                    'Description' : 'The unique ID of the entry. Referenced in '
                                    'master/detail setups as well as triggers.'},
                'field' : {
                    'Typecast' : GTypecast.name,
                    'Label' : _('Field (Database)'),
                    'Description' : 'The name of the field in the datasource to '
                                    'which this widget is tied.'},
                'datatype' : {
                    'Label' : u_("Datatype"),
                    'Description' : u_("The type of data stored in this field."),
                    'Typecast' : GTypecast.name,
                    'ValueSet' : {
                        'text' : {
                            'Label' : u_("Text")},
                        'number' : {
                            'Label' : u_('Number')},
                        'date' : {
                            'Label' : u_("Date")},
                        'time' : {
                            'Label' : u_("Time")},
                        'datetime' : {
                            'Label' : u_("Date and time")},
                        'boolean' : {
                            'Label' : u_('Boolean')},
                        'raw' : {
                            'Label' : u_('Raw data')}},
                    'Default' : 'raw'},
                'length' : {
                    'Label' : u_("Length"),
                    'Description' : u_("Maximum length of data stored in this field. Applies "
                                       "only to fields with a datatype of 'string' or 'number'. "
                                       "For numbers, this is the total number of digits, "
                                       "including the fractional digits."),
                    'Typecast' : GTypecast.whole},
                'scale' : {
                    'Label' : u_("Scale"),
                    'Description' : u_("Number of fractional digits. Applies only to fields with "
                                       "a datatype of 'number'."),
                    'Typecast' : GTypecast.whole},
                'case' : {
                    'Label' : u_("Case"),
                    'Description' : u_("Convert the value to uppercase/lowercase or leave it as "
                                       "it is. Applies only to fields with a datatype of "
                                       "'string'."),
                    'Typecast' : GTypecast.name,
                    'ValueSet' : {
                        'mixed' : {
                            'Label' : _('Mixed case')},
                        'upper' : {
                            'Label' : _('Upper case')},
                        'lower' : {
                            'Label' : _('Lower case')}},
                    'Default' : 'mixed'},
                'required' : {
                    'Label' : u_("Required"),
                    'Description' : u_("If set, empty values can not be stored in this field."),
                    'Typecast' : GTypecast.boolean,
                    'Default' : False},
                'maxLength' : {
                    'Typecast' : GTypecast.whole,
                    'Deprecated' : 'Use length'},
                'minLength' : {
                    'Typecast' : GTypecast.whole,
                    'Label' : _('Min Text Length'),
                    'Description' : 'The minimum number of characters the user must '
                                    'enter into the entry.',
                    'Default' : 0
                },
                'max_length' : {
                    'Typecast' : GTypecast.whole,
                    'Deprecated' : 'Use length',
                    'Description' : 'The maximum number of characters the user is '
                                    'allowed to enter into the entry.'},
                'min_length' : {
                    'Typecast' : GTypecast.whole,
                    'Deprecated' : 'Use minLength',
                    'Description' : 'The minimum number of characters the user must '
                                    'enter into the entry.',
                    'Default' : 0
                },
                'typecast' : {
                    'Typecast' : GTypecast.name,
                    'Deprecated' : 'Use "type".'},
                'value' : {
                    'Typecast' : GTypecast.text,
                    'Deprecated' : 'Use default="..." instead',
                    'Description' : 'Deprecated'},
                'fk_source' : {
                    'References' : 'datasource.name',
                    'Label' : _('F/K Datasource'),
                    'Typecast' : GTypecast.name,
                    'Description' : 'Source table that the foreign key links to.'},
                'fk_key' : {
                    'Label' : _('F/K Bound Field'),
                    'Typecast' : GTypecast.name,
                    'Description' : 'The table column (field) in the foreign key '
                                    'source table that the foreign key links to.'},
                'fk_description' : {
                    'Typecast' : GTypecast.name,
                    'Label' : _('F/K Description Field'),
                    'Description' : 'The description used if a style of dropdown is '
                                    'selected. This field\'s value is displayed in '
                                    'the dropdown but the foreign_key value is '
                                    'actually stored in the field. This allows you '
                                    'to display something like the full name of a '
                                    'US state but only store it\'s 2 character '
                                    'abbreviation.'},
                'fk_refresh' : {
                    'Typecast' : GTypecast.name,
                    'Label' : _('F/K Refresh Method'),
                    'ValueSet' : {
                        'startup' : {
                            'Label' : _('On form startup')},
                        'change' : {
                            'Label' : _('On field modification')},
                        'commit' : {
                            'Label' : _('On commit')}},
                    'Default' : 'startup',
                    'Description' : 'Decides when the foreign key should be '
                                    'refreshed.'},
                'default' : {
                    'Typecast' : GTypecast.text,
                    'Label' : _('Default (New Records)'),
                    'Description' : 'The default value for this field when a new '
                                    'record is created. '
                                    'If the field is visible the user can override '
                                    'the value.'},
                'defaultToLast' : {
                    'Typecast' : GTypecast.boolean,
                    'Label' : _('Default to last entry'),
                    'Default' : False,
                    'Description' : 'If {Y}, then new records will default to the '
                                    'last value the user entered for this field. If '
                                    'no new values have been entered, then defaults '
                                    'back to the normal {default} setting.'},
                'queryDefault' : {
                    'Typecast' : GTypecast.text,
                    'Label' : _('Default (Querying)'),
                    'Description' : 'The field will be populated with this value '
                                    'automatically when a query is requested. If '
                                    'the field is visible the user can still '
                                    'override the value.'},
                'query_casesensitive' : {
                    'Typecast' : GTypecast.boolean,
                    'Label' : _('Perform queries case-sensitive'),
                    'Default' : False,
                    'Description' : 'If "N", the entry widget ignores the case '
                                    'of the information entered into the query mask.'},
                'editable' : {
                    'Description' : 'Only allow this object to be edited if it '
                                    'is currently empty.',
                    'Label' : _('Allow Editing'),
                    'ValueSet' : {
                        'Y' : {
                            'Label' : _('Yes')},
                        'N' : {
                            'Label' : _('No')},
                        'null' : {
                            'Label' : _('Null Only')},
                        'update' : {
                            'Label' : _('Update Only')},
                        'new' : {
                            'Label' : _('New Records Only')}},
                    'Typecast' : GTypecast.text,
                    'Default' : 'Y'},
                'queryable' : {
                    'Description' : 'Is this object queryable?',
                    'Label' : _('Allow Query'),
                    'Typecast' : GTypecast.boolean,
                    'Default' : True},
                'autoquery' : {
                    'Description' : 'If {Y} then any changes in this field will '
                                    'cause the form to automatically query and '
                                    'populate itself with matching records.  If '
                                    '{New} it will only automatically query if '
                                    'the form is currenly completely empty.  If '
                                    '{N} then no automatic query will be performed.',
                    'Label' : _('Automatic Query'),
                    'ValueSet' : {
                        'Y' : {
                            'Label' : _('Yes')},
                        'N' : {
                            'Label' : _('No')},
                        'new' : {
                            'Label' : _('Empty forms only')}},
                    'Typecast' : GTypecast.text,
                    'Default' : 'N'},
                'ltrim' : {
                    'Label' : _('Trim left spaces'),
                    'Description' : 'Trim extraneous space at '
                                    'beginning of user input.',
                    'Typecast' : GTypecast.boolean,
                    'Default' : False},
                'rtrim' : {
                    'Label' : _('Trim right spaces'),
                    'Description' : 'Trim extraneous space at end '
                                    'of user input.',
                    'Typecast' : GTypecast.boolean,
                    'Default' : True}},

            'ParentTags' : ('block', ),
            'Label' : u_('Field'),
            'Description' : 'A field represents a column in the database table '
                            'designated by the block.'},
        # If you implement a new entry "style", add to the entryStyles
        # structure after this list
        'entry' : {
            'BaseClass' : GFObjects.GFEntry,
            'Attributes' : {
                'name' : {
                    'Unique' : True,
                    'Typecast' : GTypecast.name,
                    'Description' : 'The unique ID of the entry.'},
                'label' : {
                    'Required' : False,
                    'Typecast' : GTypecast.text,
                    'Description' : 'The optional label displayed next to checkbox.'},
                'field' : {
                    'Typecast' : GTypecast.name,
                    'References' : 'field.name',
                    'Required' : True,
                    'Description' : 'The name of the field that this ties to.'},
                'block' : {
                    'Typecast' : GTypecast.name,
                    'Required' : False,
                    'References' : 'block.name',
                    'Description' : 'The name of the block that this ties to.'},
                'focusorder' : {
                    'Typecast' : GTypecast.whole,
                    'Label' : _('Focus Order'),
                    'Description' : 'Defines what order the focus moves through '
                                    'entries.'},
                'rows' : {
                    'Typecast' : GTypecast.whole,
                    'Description' : 'Overrides the rows setting defined at the '
                                    'block level.'},
                'rowSpacer' : {
                    'Typecast' : GTypecast.whole,
                    'Label' : _('Row Spacing'),
                    'Description' : 'Overrides the rowSpacer setting at the '
                                    'block level.'},
                'navigable' : {
                    'Typecast' : GTypecast.boolean,
                    'Description' : 'If false, the user will be unable to navigate '
                                    'to this entry. Triggers can still '
                                    'alter the value though.',
                    'Default' : True},
                'hidden' : {
                    'Typecast' : GTypecast.boolean,
                    'Default' : False,
                    'Deprecated' : 'Use a field without entry instead'},
                'style' : {
                    'Typecast' : GTypecast.name,
                    'ValueSet' : {
                        'auto' : {
                            'Label' : _('Automatic')},
                        'default' : {
                            'Label' : _('Default')},
                        'password' : {
                            'Label' : _('Password/Hidden')},
                        'dropdown' : {
                            'Label' : _('Dropdown/Combo box')},
                        'listbox' : {
                            'Label' : _('Listbox')},
                        'radiobox' : {
                            'Label' : _('Radiobox')},
                        'checkbox' : {
                            'Label' : _('Checkbox')},
                        'multiline' : {
                            'Label' : _('Multiline-Edit')},
                        'label' : {
                            'Label' : _('Label (non-editable)')}},
                    'Default' : 'auto',
                    'Description' : 'The style of entry widget requested. '
                                    'Currently either {text}, {label}, {checkbox}, '
                                    '{listbox}, or {dropdown}. To use {listbox} or '
                                    '{dropdown} you are required to use both the '
                                    '{fk_source}, {fk_key}, and {fk_description} '
                                    'attributes. The {label} style implies the '
                                    '{readonly} attribute.'},
                'maxitems' : {
                    'Typecast' : GTypecast.whole,
                    'Default' : 2
                    ,
                    'Label' : _('Max item count'),
                    'Description' : 'For radiobox style only.'
                                    'Because max item count is static'},
                'formatmask' : {
                    'Typecast' : GTypecast.text,
                    'Label' : _('Format Mask'),
                    'Description' : 'TODO'},
                'inputmask' : {
                    'Typecast' : GTypecast.text,
                    'Label' : _('Input Mask'),
                    'Description' : 'Defines how the user will edit a field\'s '
                                    'value.'},
                'displaymask' : {
                    'Label' : _('Display Mask'),
                    'Typecast' : GTypecast.text,
                    'Description' : 'Defines how the field data will be formatted '
                                    'for display.'}},

            'Positionable' : True,
            'ParentTags' : ('page', 'hbox', 'vbox', 'box', 'gridline', 'table'),
            'Label' : u_('Entry'),
            'Description' : 'An {entry} is the visual counterpart to a {field}, '
                            'it defines how the data in a field will be displayed '
                            'and how it can be edited.'},
        'scrollbar' : {
            'BaseClass' : GFObjects.GFScrollBar,
            'Attributes' : {
                'name' : {
                    'Unique' : True,
                    'Typecast' : GTypecast.name,
                    'Description' : 'The unique name of the scrollbar.'},
                'scrollrows' : {
                    'Typecast' : GTypecast.whole,
                    'Description' : 'Defaults to the rows setting defined at the '
                                    'block level.'},
                'block' : {
                    'Required' : True,
                    'Typecast' : GTypecast.name,
                    'References' : 'block.name',
                    'Description' : 'The {block} to which this scrollbar scrolls.'}},

            'Positionable' : True,
            'ParentTags' : ('page', 'vbox', 'hbox', 'box'),
            'Label' : u_('Scrollbar'),
            'Description' : 'A scrollbar is a visual element that lets the user '
                            'move vertically layout elements linked to it.'},
        'vbox' : {
            'BaseClass' : GFObjects.GFVBox,
            'Attributes' : {
                'name' : {
                    'Unique' : True,
                    'Typecast' : GTypecast.name,
                    'Description' : 'The unique name of the box.'},
                'label' : {
                    'Typecast' : GTypecast.text,
                    'Description' : 'An optional text label that will be displayed '
                                    'on the border.'},
                'block' : {
                    'Required' : False,
                    'Typecast' : GTypecast.name,
                    'References' : 'block.name',
                    'Description' : 'The {block} to which this scrollbar scrolls.'},
            },
            'Positionable' : True,
            'ParentTags' : ('page', 'vbox', 'hbox', 'box'),
            'Label' : u_('Box (Vertical)'),
            'Description' : 'A box is a visual element that draws a box around '
                            'other visual elements, thus providing logical '
                            'separation for them.'},
        'hbox' : {
            'BaseClass' : GFObjects.GFHBox,
            'Attributes' : {
                'name' : {
                    'Unique' : True,
                    'Typecast' : GTypecast.name,
                    'Description' : 'The unique name of the box.'},
                'label' : {
                    'Typecast' : GTypecast.text,
                    'Description' : 'An optional text label that will be displayed '
                                    'on the border.'},
                'block' : {
                    'Required' : False,
                    'Typecast' : GTypecast.name,
                    'References' : 'block.name',
                    'Description' : 'The {block} to which this scrollbar scrolls.'},
            },
            'Positionable' : True,
            'ParentTags' : ('page', 'vbox', 'hbox', 'box'),
            'Label' : u_('Box (Horizontal)'),
            'Description' : 'A box is a visual element that draws a box around '
                            'other visual elements, thus providing logical '
                            'separation for them.'},
        'box' : {
            'BaseClass' : GFObjects.GFBox,
            'Attributes' : {
                'name' : {
                    'Unique' : True,
                    'Typecast' : GTypecast.name,
                    'Description' : 'The unique name of the box.'},
                'label' : {
                    'Typecast' : GTypecast.text,
                    'Description' : 'An optional text label that will be displayed '
                                    'on the border.'},
                'focusorder' : {
                    'Typecast' : GTypecast.whole,
                    'Description' : 'Defines what order the focus moves through '
                                    'entries.'}},

            'Positionable' : True,
            'ParentTags' : ('page', 'box'),
            'Label' : u_('Box'),
            'Description' : u_('A box is a visual element that draws a box around '
                               'other visual elements, thus providing logical '
                               'separation for them.')},
        'grid' : {
            'BaseClass' : GFObjects.GFGrid,
            'Attributes' : {
                'name' : {
                    'Unique' : True,
                    'Typecast' : GTypecast.name,
                    'Description' : 'The unique ID of the grid.'},
                'block' : {
                    'Required' : False,
                    'Typecast' : GTypecast.name,
                    'Description' : 'The block for this grid.'},
                'rows' : {
                    'Typecast' : GTypecast.whole,
                    'Description' : u_('Overrides the rows setting defined at the '
                                       'block level.')},
            },
            'Positionable' : True,
            'ParentTags' : ('page', 'box', 'hbox', 'vbox'),
            'Label' : u_('Grid'),
            'Description' : u_('A grid is a layout container grouping fields into repeating rows.')},
        'gridline' : {
            'BaseClass' : GFObjects.GFGridLine,
            'Attributes' : {
                'name' : {
                    'Unique' : True,
                    'Typecast' : GTypecast.name,
                    'Description' : 'The unique ID of the grid.'},
            },
            'Positionable' : True,
            'ParentTags' : ('grid'),
            'Label' : u_('Grid Row'),
            'Description' : u_('Contains all elements of a single line in a grid')},
        'table' : {
            'BaseClass' : GFObjects.GFTable,
            'Attributes' : {
                'name' : {
                    'Unique' : True,
                    'Typecast' : GTypecast.name,
                    'Description' : 'The unique ID of the table.'},
                'block' : {
                    'Required' : False,
                    'Typecast' : GTypecast.name,
                    'Description' : 'The block for this table.'},
                #'rows': {
                #   'Typecast': GTypecast.whole,
                #   'Description': u_('Overrides the rows setting defined at the '
                #                     'block level.')},
            },
            #'Positionable': True,
            'ParentTags' : ('page', 'box', 'hbox', 'vbox'),
            'Label' : u_('Table'),
            'Description' : u_('A table as component')},
        'image' : {
            'BaseClass' : GFObjects.GFImage,
            'Attributes' : {
                'name' : {
                    'Unique' : True,
                    'Typecast' : GTypecast.name,
                    'Description' : 'The unique name of the image.'},
                'field' : {
                    'Typecast' : GTypecast.name,
                    'References' : 'block.name>field.name',
                    'Required' : True,
                    'Description' : 'The name of the field that this ties to.'},
                'block' : {
                    'Typecast' : GTypecast.name,
                    'References' : 'block.name',
                    'Required' : True,
                    'Description' : 'The name of the block that this ties to.'},
                'type' : {
                    'Typecast' : GTypecast.name,
                    'ValueSet' : {
                        'URL' : {
                            'Label' : _('Field contains the URL of the image')},
                        'PIL' : {
                            'Label' : _('Field contains a PIL encoding of the image')}},
                    'Default' : "URL",
                    'Description' : 'The type of image reference. Can be {URL} '
                                    'for a url reference, or {PIL} for an '
                                    'embedded image.'},
                'fit' : {
                    'Typecast' : GTypecast.name,
                    'ValueSet' : {
                        'none' : {
                            'Label' : _('Full-size image (no scaling)')},
                        'width' : {
                            'Label' : _('Scale to width')},
                        'height' : {
                            'Label' : _('Scale to height')},
                        'both' : {
                            'Label' : _('Scale width and height (may distort image)')},
                        'auto' : {
                            'Label' : _('Use a best-fit algorithm')}},
                    'Default' : "none",
                    'Description' : 'Defines how the image will fill the space '
                                    'provided for it (crop parts outside borders, '
                                    'or stretch width/height/both to fit into '
                                    'given boundaries).'},
                'editable' : {
                    'Description' : 'Only allow this object to be edited if it '
                                    'is currently empty.',
                    'Label' : _('Allow Editing'),
                    'ValueSet' : {
                        'Y' : {
                            'Label' : _('Yes')},
                        'N' : {
                            'Label' : _('No')},
                        'null' : {
                            'Label' : _('Null Only')},
                        'update' : {
                            'Label' : _('Update Only')},
                        'new' : {
                            'Label' : _('New Records Only')}},
                    'Typecast' : GTypecast.text,
                    'Default' : 'Y'},
                'label' : {
                    'Required' : False,
                    'Typecast' : GTypecast.text,
                    'Description' : 'Label displayed next or above to the image'},
                'focusorder' : {
                    'Typecast' : GTypecast.whole,
                    'Description' : 'Defines what order the focus moves through '
                                    'entries.'}},

            'Positionable' : True,
            'ParentTags' : ('page', 'vbox', 'hbox', 'box'),
            'Label' : u_('Image'),
            'Description' : 'Displays an image.'},
        'component' : {
            'BaseClass' : GFObjects.GFComponent,
            'Attributes' : {
                'name' : {
                    'Unique' : True,
                    'Typecast' : GTypecast.name,
                    'Description' : 'The unique name of the component.'},
                'field' : {
                    'Typecast' : GTypecast.name,
                    'References' : 'block.name>field.name',
                    'Required' : True,
                    'Description' : 'The name of the field that this ties to.'},
                'block' : {
                    'Typecast' : GTypecast.name,
                    'References' : 'block.name',
                    'Required' : True,
                    'Description' : 'The name of the block that this ties to.'},
                'mimetype' : {
                    'Typecast' : GTypecast.name,
                    'Required' : True,
                    'Description' : 'TODO'},
                'type' : {
                    'Typecast' : GTypecast.name,
                    'ValueSet' : {
                        'URL' : {
                            'Label' : _('Field contains the URL of the component')},
                        'Base64' : {
                            'Label' : _("Field contains the data of the "
                                        "component in Base64 encoding")}},
                    'Default' : "URL",
                    'Description' : 'TODO'},
                'focusorder' : {
                    'Typecast' : GTypecast.whole,
                    'Description' : 'Defines what order the focus moves through '
                                    'entries.'}},

            'Positionable' : True,
            'ParentTags' : ('page', 'vbox', 'hbox', 'box'),
            'Label' : u_('Embedded Component'),
            'Description' : 'TODO'},
        'button' : {
            'BaseClass' : GFObjects.GFButton,
            'Importable' : True,
            'Attributes' : {
                'name' : {
                    'Unique' : True,
                    'Typecast' : GTypecast.name,
                    'Description' : 'A unique ID for the widget. Useful for '
                                    'importable buttons. '},
                'navigable' : {
                    'Description' : 'Can this button be navigated?',
                    'Label' : _('Navigable'),
                    'Typecast' : GTypecast.boolean,
                    'Default' : True},
                'block' : {
                    'Typecast' : GTypecast.name,
                    'References' : 'block.name',
                    'Description' : 'The (optional) name of the block that this '
                                    'ties to. If a button is associated with '
                                    'a block, then the button honors '
                                    'the block\'s rows= value.'},
                'rows' : {
                    'Typecast' : GTypecast.whole,
                    'Description' : 'Overrides the rows setting defined at the '
                                    'block level. '},
                'rowSpacer' : {
                    'Typecast' : GTypecast.whole,
                    'Label' : _('Row Spacing'),
                    'Description' : 'Overriders the rowSpace setting defined at the '
                                    'block level.'},
                'focusorder' : {
                    'Typecast' : GTypecast.whole,
                    'Description' : 'Defines what order the focus moves through '
                                    'entries.'},
                'label' : {
                    'Typecast' : GTypecast.name,
                    'Description' : 'The text that should appear on the button'},
                'image' : {
                    'Typecast' : GTypecast.text,
                    'Description' : 'Path to image that should appear on the button'},
                'imagemask' : {
                    'Typecast' : GTypecast.text,
                    'Description' : 'Mask color for image, e. g. wx.BLUE'},
                'action' : {
                    'Typecast' : GTypecast.name,
                    'Description' : 'Action to be executed when the button is fired'}},
            'Positionable' : True,
            'ParentTags' : ('page', 'vbox', 'hbox', 'box', 'gridline'),
            'Label' : u_('Button'),
            'Description' : 'A visual element with text placed on it, that '
                            'the user can push or click, and that event can run '
                            'a bound trigger.'},
        'tree' : {
            'BaseClass' : GFObjects.GFTree,
            'Attributes' : {
                'name' : {
                    'Unique' : True,
                    'Typecast' : GTypecast.name,
                    'Description' : 'Unique name of the tree'},
                'datasource' : {
                    'References' : 'datasource.name',
                    'Typecast' : GTypecast.name,
                    'Description' : 'The name of a datasource'},
                'block' : {
                    'Typecast' : GTypecast.name,
                    'Required' : False,
                    'References' : 'block.name',
                    'Description' : 'The name of the block the tree ties to.'},
                'fld_id' : {
                    'Label' : _('Own ID field'),
                    'Typecast' : GTypecast.name,
                    'Required' : True,
                    'Description' : 'The field containing the TreeViewItem ID'},
                'fld_parent' : {
                    'Label' : _('Parent ID field'),
                    'Typecast' : GTypecast.name,
                    'Required' : True,
                    'Description' : 'The field containing the TreeViewItem parent'},
                'nodename' : {
                    'Label' : _('Tree node name pattern'),
                    'Typecast' : GTypecast.name,
                    'Required' : True,
                    'Description' : 'Tree node name pattern. Use %(field) to reference field'},
                'rootid' : {
                    'Label' : _('Root id'),
                    'Typecast' : GTypecast.name,
                    'Required' : False,
                    'Description' : 'Root id, default is null',
                    'Default' : "None"},
            },
            'Positionable' : True,
            'ParentTags' : ('page', 'box', 'hbox', 'vbox'),
            'Description' : 'Tree-View of a table',
        },
        'options' : {
            'BaseClass' : GFObjects.GFOptions,
            'UsableBySiblings' : True,
            'ParentTags' : ('form', 'dialog'),
            'Label' : u_('Options'),
            'Description' : 'TODO'},
        'option' : {
            'BaseClass' : GFObjects.GFOption,
            'Attributes' : {
                'name' : {
                    'Required' : True,
                    'Typecast' : GTypecast.name,
                    'Description' : 'TODO'},
                'value' : {
                    'Typecast' : GTypecast.text,
                    'Description' : 'TODO'}},

            'MixedContent' : True,
            'ParentTags' : ('options', ),
            'Label' : u_('Option'),
            'Description' : 'TODO'},
        'title' : {
            'BaseClass' : GFObjects.GFOption,
            'Attributes' : {
                'name' : {
                    'Typecast' : GTypecast.name,
                    'ValueSet' : {
                        'title' : {
                        }},
                    'Default' : 'title',
                    'Description' : 'TODO'},
                'value' : {
                    'Typecast' : GTypecast.text,
                    'Description' : 'TODO'}},

            'MixedContent' : True,
            'SingleInstance' : True,
            'Deprecated' : 'Use the <form> attribute "title" instead.',
            'ParentTags' : ('options', ),
            'Label' : u_('Form Title'),
            'Description' : 'TODO'},
        'name' : {
            'BaseClass' : GFObjects.GFOption,
            'Attributes' : {
                'name' : {
                    'Typecast' : GTypecast.name,
                    'ValueSet' : {
                        'name' : {
                        }},
                    'Default' : 'name',
                    'Description' : 'TODO'},
                'value' : {
                    'Typecast' : GTypecast.text,
                    'Description' : 'TODO'}},

            'MixedContent' : True,
            'SingleInstance' : True,
            'ParentTags' : ('options', ),
            'Label' : u_('Name'),
            'Description' : 'TODO'},
        'author' : {
            'BaseClass' : GFObjects.GFOption,
            'Attributes' : {
                'name' : {
                    'Typecast' : GTypecast.name,
                    'ValueSet' : {
                        'author' : {
                        }},
                    'Default' : 'author',
                    'Description' : 'TODO'},
                'value' : {
                    'Typecast' : GTypecast.text,
                    'Description' : 'TODO'}},

            'MixedContent' : True,
            'SingleInstance' : True,
            'ParentTags' : ('options', ),
            'Label' : u_('Form Author'),
            'Description' : 'TODO'},
        'description' : {
            'BaseClass' : GFObjects.GFOption,
            'Attributes' : {
                'name' : {
                    'Typecast' : GTypecast.name,
                    'ValueSet' : {
                        'description' : {
                        }},
                    'Default' : 'description',
                    'Description' : 'TODO'},
                'value' : {
                    'Typecast' : GTypecast.text,
                    'Description' : 'TODO'}},

            'MixedContent' : True,
            'SingleInstance' : True,
            'ParentTags' : ('options', ),
            'Label' : u_('Description'),
            'Description' : 'TODO'},
        'version' : {
            'BaseClass' : GFObjects.GFOption,
            'Attributes' : {
                'name' : {
                    'Typecast' : GTypecast.name,
                    'ValueSet' : {
                        'version' : {
                        }},
                    'Default' : 'version',
                    'Description' : 'TODO'},
                'value' : {
                    'Typecast' : GTypecast.text,
                    'Description' : 'TODO'}},

            'MixedContent' : True,
            'SingleInstance' : True,
            'ParentTags' : ('options', ),
            'Label' : u_('Version'),
            'Description' : 'TODO'},
        'tip' : {
            'BaseClass' : GFObjects.GFOption,
            'Attributes' : {
                'name' : {
                    'Typecast' : GTypecast.name,
                    'ValueSet' : {
                        'tip' : {
                        }},
                    'Default' : 'tip',
                    'Description' : 'TODO'},
                'value' : {
                    'Typecast' : GTypecast.text,
                    'Description' : 'TODO'}},

            'MixedContent' : True,
            'SingleInstance' : True,
            'ParentTags' : ('options', ),
            'Label' : u_('Tip'),
            'Description' : 'TODO'},
        'parameter' : {
            'BaseClass' : GFObjects.GFParameter,
            'Attributes' : {
                'name' : {
                    'Label' : u_("Name"),
                    'Description' : u_("Unique name of the parameter."),
                    'Typecast' : GTypecast.name,
                    'Required' : True,
                    'Unique' : True},
                'datatype' : {
                    'Label' : u_("Datatype"),
                    'Description' : u_("The type of data for this parameter."),
                    'Typecast' : GTypecast.name,
                    'ValueSet' : {
                        'text' : {
                            'Label' : u_("Text")},
                        'number' : {
                            'Label' : u_('Number')},
                        'date' : {
                            'Label' : u_("Date")},
                        'time' : {
                            'Label' : u_("Time")},
                        'datetime' : {
                            'Label' : u_("Date and time")},
                        'boolean' : {
                            'Label' : u_('Boolean')},
                        'raw' : {
                            'Label' : u_('Raw data')}},
                    'Default' : 'raw'},
                'length' : {
                    'Label' : u_("Length"),
                    'Description' : u_("Maximum length of data stored in this parameter. Applies "
                                       "only to parameters with a datatype of 'string' or "
                                       "'number'. For numbers, this is the total number of "
                                       "digits, including the fractional digits."),
                    'Typecast' : GTypecast.whole},
                'scale' : {
                    'Label' : u_("Scale"),
                    'Description' : u_("Number of fractional digits. Applies only to parameters "
                                       "with a datatype of 'number'."),
                    'Typecast' : GTypecast.whole},
                'required' : {
                    'Label' : u_("Required"),
                    'Description' : u_("If set, it is obligatory to provide this parameter "
                                       "to run the form."),
                    'Typecast' : GTypecast.boolean,
                    'Default' : False},
                'default' : {
                    'Label' : u_("Default value"),
                    'Description' : u_("Default value for the parameter, if the user does "
                                       "not provide a value for it."),
                    'Typecast' : GTypecast.text},
                'description' : {
                    'Label' : u_("Description"),
                    'Description' : u_("Description of the parameter for the help text."),
                    'Typecast' : GTypecast.text},
                'type' : {
                    'Typecast' : GTypecast.name,
                    'Deprecated' : 'Use "datatype" instead.'}},
            'ParentTags' : ('form', 'dialog'),
            'Label' : u_('Parameter'),
            'Description' : 'A form can get parameters from the outer world '
                            'or a calling form, and can pass values back too '
                            'in these parameters.'},
    }#
    # Create the dialog alias for the forms
    #
    copy._deepcopy_dispatch[types.FunctionType] = copy._deepcopy_atomiccopy._deepcopy_dispatch[types.ClassType] = copy._deepcopy_atomiccopy._deepcopy_dispatch[type(int)] = copy._deepcopy_atomicdialog = copy.deepcopy(xmlElements['form'])dialog['Required'] = Falsedialog['SingleInstance'] = Falsedialog['Importable'] = Truedialog['Attributes']['style']['Default'] = 'dialog'dialog['ParentTags'] = ('form', 'dialog')dialog['Label'] = u_('Dialog')xmlElements.update({
        'dialog' : dialog})#
    # Add DataSource elements
    #
    datasourceElems = GDataSource.getXMLelements(updates = {
        'datasource' : {
            'BaseClass' : GFObjects.GFDataSource, 'ParentTags' : ('form', 'dialog')},
        'cparam' : {
            'BaseClass' : GFObjects.GFCParam}})# TODO: This may get moved to GCommon's datasources,
    # TODO: but first have to determine if it will confuse
    # TODO: development for other tools.
    datasourceElems['datasource']['Attributes'].update({
        'detailmin' : {
            'Label' : _('M/D Min Child Rows'),
            'Description' : 'If this datasource is the child in a '
                            'master/detail relationship, this property '
                            'specifies the minimum number of child '
                            'records that must be present for a commit '
                            'to be valid. Usually, this is 0 (for '
                            'one-to-many relationships) or 1 '
                            '(for one-to-one relationships).',
            'Default' : 0
            ,
            'Typecast' : GTypecast.whole},
        'detailmax' : {
            'Label' : _('M/D Max Child Rows'),
            'Description' : 'If this datasource is the child in a '
                            'master/detail relationship, this property '
                            'specifies the maximum number of child '
                            'records that can be created. Usually, this '
                            'is either omitted (for one-to-many '
                            'relationships) or 1 (for one-to-one '
                            'relationships).',
            'Typecast' : GTypecast.whole}})