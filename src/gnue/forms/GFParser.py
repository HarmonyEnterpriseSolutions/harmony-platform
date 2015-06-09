#
# This file is part of GNU Enterprise.
#
# GNU Enterprise is free software; you can redistribute it
# and/or modify it under the terms of the GNU General Public
# License as published by the Free Software Foundation; either
# version 2, or (at your option) any later version.
#
# GNU Enterprise is distributed in the hope that it will be
# useful, but WITHOUT ANY WARRANTY; without even the implied
# warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR
# PURPOSE. See the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public
# License along with program; see the file COPYING. If not,
# write to the Free Software Foundation, Inc., 59 Temple Place
# - Suite 330, Boston, MA 02111-1307, USA.
#
# Copyright 2000-2007 Free Software Foundation
#
# $Id: GFParser.py,v 1.96 2015/03/12 17:39:27 oleg Exp $

"""
Class that contains a sax based xml processor for GNUe forms

NOTE: Designer uses the 'Positionable' attribute. It is specific to
forms+designer and is not part of the GParser spec. If set to
true, then this object is a visible, movable, sizable attribute.
"""

from gnue.common.datasources import GDataSource
from gnue.common.definitions import GParser
from gnue.common.formatting import GTypecast
from gnue.common.logic import usercode, GTrigger

import copy, types





########
########  Please keep this file neat !!!
########



root_tag = 'form'


##
##
##
def loadFile (buffer, instance, initialize=True, url=None, check_required=True):
	"""
	This method loads a form from an XML file and returns
	a GFForm object.  If initialize is 1 (default), then
	the form is initialized and ready to go.

	(initialize=0 is currently not used -- will probably
	be used in the Forms Designer package where we will
	not want the loaded form to connect to databases, etc)
	"""
	return GParser.loadXMLObject (buffer, xmlFormsHandler, 'GFForm', root_tag,
		initialize,
		attributes={"_instance": instance,
			"_connections": instance.connections},
		url=url, checkRequired=check_required)


xmlElements = None

def getXMLelements():

	global xmlElements

	if xmlElements == None:
		from gnue.forms import GFObjects, GFLibrary, GFForm
		from gnue.forms.GFObjects import commanders

		xmlElements = {
			'form': {
				'BaseClass': GFForm.GFForm,
				'Required': True,
				'SingleInstance': True,
				'Label': _('Form'),
				'Attributes': {
					'title': {
						'Typecast': GTypecast.text,
						'Default': '',
						'Label': _('Title'),
						'Description': _('The title of the form.') },
					'name': {
						'Unique': True,
						'Typecast': GTypecast.name,
						'Label': _('Name'),
						'Description': _('A unique name or ID for the form.'),
					},
					'style': {
						'Typecast': GTypecast.name,
						'Label': _('Style'),
						'ValueSet': {
							'normal': {'Label': _('Normal')},
							'dialog': {'Label': _('Dialog')} },
						'Default': 'normal',
						'Description': _('Display as normal or dialog-style window.'),
					},
					'windowStyle': {
						'Typecast': GTypecast.names,
						'Label': _('Window style'),
						'Default': '',
						'Description': _(
							'Window style. String is combination of comma delimited\n'
							'    MINIMIZE_BOX\n'
							'    MAXIMIZE_BOX\n'
							'    CLOSE_BOX\n'
							'    RESIZEABLE\n'
							'    CAPTION\n'
							'    MAXIMIZE\n'
							'\n'
							'Default for style "normal":\n'
							'    "CAPTION, MINIMIZE_BOX, MAXIMIZE_BOX, CLOSE_BOX, RESIZE"\n'
							'Default for style "dialog":\n'
							'    CAPTION, CLOSE_BOX, RESIZE\n'
						),
					},
					'description': {
						'Typecast': GTypecast.text,
						'Description': 'Text to display in a tooltip',
					},
				},
				'ParentTags': None,
				'Description': _(
					'Top-level element that encloses all the logic '
					'and visuals that the user interface will show '
					'to the user.'
				),
			},

			'menu': {
				'Description': _("A menu or submenu containing menu items and/or submenus"),
				'BaseClass'  : commanders.GFMenu,
				'Importable': True,
				'ParentTags' : ('form','dialog','menu','tree','table','treelist','button'),
				'Label': _('Menu'),
				'Attributes' : {
					'name': {
						'Label'      : _("Name"),
						'Description': _("Name of this element"),
						'Typecast'   : GTypecast.name,
						'Unique'     : True,
					},
					'label': {
						'Label'      : _("Label"),
						'Description': _("Text to use if this is a submenu"),
						'Typecast'   : GTypecast.text,
					},
				},
			},
			'menuitem': {
				'Description': _(
					"A menu item that fires a trigger when selected"),
				'BaseClass'  : commanders.GFMenuItem,
				'Label': _('Menu Item'),
				'ParentTags' : ('menu',),
				'Attributes' : {
					'name': {
						'Label'      : _("Name"),
						'Description': _("Name of this element"),
						'Typecast'   : GTypecast.name,
						'Unique'     : True,
					},
					'icon': {
						'Label'      : _("Icon"),
						'Description': _("Icon to display besides this menu item"),
						'Typecast'   : GTypecast.name
					},
					'label': {
						'Label'      : _("Label"),
						'Description': _("Text to use for this menu item"),
						'Typecast'   : GTypecast.text,
					},
					'description': {
						'Label'      : _("Description"),
						'Description': _("Text to display in the status bar for this menu item"),
						'Typecast'   : GTypecast.text,
					},
					'action': {
						'Label'      : _("Action"),
						'Description': _(
							"Name of the trigger to run whenever this menu "
							"item is selected"),
						'Typecast'   : GTypecast.name,
						'References' : 'trigger.name'},
					'action_off': {
						'Label'      : _("Action Off"),
						'Description': _(
							"Name of the trigger to run whenever this menu "
							"item is switched to off"),
						'Typecast'   : GTypecast.name,
						'References' : 'trigger.name'},
					'hotkey': {
						'Label'      : _("Hotkey"),
						'Description': _("Hotkey to assign to this menu item"),
						'Typecast'   : GTypecast.text},
					'state': {
						'Label'      : _("State"),
						'Description': _(
							"Determines whether this menu item will be "
							"switched on by default"),
						'Typecast'   : GTypecast.boolean,
						'Default'    : False},
					'enabled': {
						'Label'      : _("Enabled"),
						'Description': _(
							"Determines whether this menu item will be "
							"enabled by default"),
						'Typecast'   : GTypecast.boolean,
						'Default'    : True}}},
			'toolbar': {
				'Importable': True,
				'Description': _("A toolbar containing tool buttons"),
				'BaseClass'  : commanders.GFToolbar,
				'ParentTags' : ('form','dialog'),
				'Label': _('Toolbar'),
				'Attributes' : {
					'name': {
						'Label'      : _("Name"),
						'Description': _("Name of this element"),
						'Typecast'   : GTypecast.name,
						'Required'   : True,
						'Unique'     : True}}},
			'toolbutton': {
				'Description': _("A button on a toolbar"),
				'BaseClass'  : commanders.GFToolButton,
				'ParentTags' : ('toolbar',),
				'Label': _('Toolbar Button'),
				'Attributes' : {
					'name': {
						'Label'      : _("Name"),
						'Description': _("Name of this element"),
						'Typecast'   : GTypecast.name,
						'Unique'     : True},
					'icon': {
						'Label'      : _("Icon"),
						'Description': _("Icon to display on the button"),
						'Typecast'   : GTypecast.name},
					'label': {
						'Label'      : _("Label"),
						'Description': _("Text to display on the button"),
						'Typecast'   : GTypecast.text},
					'description': {
						'Label'      : _("Description"),
						'Description': _(
							"Text to display in a tooltip window"),
						'Typecast'   : GTypecast.text},
					'action': {
						'Label'      : _("Action"),
						'Description': _(
							"Name of the trigger to run whenever this button "
							"is clicked"),
						'Typecast'   : GTypecast.name,
						'References' : 'trigger.name'},
					'action_off': {
						'Label'      : _("Action Off"),
						'Description': _(
							"Name of the trigger to run whenever this button "
							"is switched to off"),
						'Typecast'   : GTypecast.name,
						'References' : 'trigger.name'},
					'state': {
						'Label'      : _("State"),
						'Description': _(
							"Determines whether this button will be switched "
							"on by default"),
						'Typecast'   : GTypecast.boolean,
						'Default'    : False},
					'enabled': {
						'Label'      : _("Enabled"),
						'Description': _(
							"Determines whether this button will be enabled "
							"by default"),
						'Typecast'   : GTypecast.boolean,
						'Default'    : True}}},

			'logic': {
				'BaseClass': GFObjects.GFLogic,
				'Importable': True,
				'SingleInstance': True,
				'ParentTags': ('form','dialog'),
				'Label': _('Logic'),
				'Description': 'Separation layer that contains "Business logic": '
				'blocks, fields, block-level and field-level triggers.'},

			'layout': {
				'BaseClass': GFObjects.GFLayout,
				'Importable': True,
				'SingleInstance': True,
				'ParentTags': ('form','dialog'),
				'Label': _('Layout'),
				'Description': 'Separation layer that contains all the '
				'visual elements on the form.' ,
				'Attributes': {
					'name': {
						'Unique': True,
						'Typecast': GTypecast.name,
						'Label': _('Name'),
						'Default': 'layout',
						'Description': 'A unique name or ID for the form.' },
				} } ,

			'block': {
				'BaseClass': GFObjects.GFBlock,
				'Importable': True,
				'Attributes': {
					'name': {
						'Required': True,
						'Unique': True,
						'Typecast': GTypecast.name,
						'Description': 'A unique ID (name) for the widget. '
						'No blocks can share '
						'the same name without causing namespace '
						'collisions in user triggers.' },
					'startup': {
						'Label': _("Startup state"),
						'Description': _(
							"State in which the block will be on form startup. "
							"'Empty' means the block is filled with a single empty "
							"record, 'full' means the block is populated with the "
							"result of a full query."),
						'Typecast': GTypecast.name,
						'ValueSet': {
							'empty': {'Label': _('Empty')},
							'full':  {'Label': _('Full')}},
						'Default': 'empty'},
					'transparent':{
						'Typecast': GTypecast.boolean,
						'Label': _('Transparent Nav'),
						'Default': True,
						'Description': 'If set, then you can tab out of the block via next- '
						'or previous-field events. Makes navigation in '
						'multiblock forms easier. If false, focus stays '
						'within a block until user explicitly moves to '
						'another block. Note that a block\'s {autoNextRecord}'
						'setting affects {transparent} behavior' },
					'autoCreate':{
						'Typecast': GTypecast.boolean,
						'Label': _('Auto Create Record'),
						'Default': True,
						'Description': 'If set, then if you attempt to go to the next record '
						'while at the last record, a new record is created.'},
					'autoNextRecord':{
						'Typecast': GTypecast.boolean,
						'Label': _('Auto Next Record'),
						'Default': False,
						'Description': 'If set, then if you tab at the end of a block, you '
						'will be taken to the next record. If the current '
						'record is empty and transparent is true, then '
						'you will be taken to the next block'},
					'autoCommit':{
						'Typecast': GTypecast.boolean,
						'Label': _('Auto Commit'),
						'Default': False,
						'Description': 'If set, then the datasource will automatically '
						'commit changes when trying to navigate out of the '
						'current record.'},
					'autoClear':{
						'Typecast': GTypecast.boolean,
						'Label': _('Auto Clear on Commit'),
						'Default': False,
						'Description': 'If set, then the block is cleared/emptied on '
						'a commit.'},
					'editable': {
						'Description': 'Can records be edited/created?',
						'Label': _('Allow Editing'),
						'ValueSet': {
							'Y': {'Label': _('Yes')},
							'N': {'Label': _('No')},
							'update': {'Label': _('Update Only')},
							'new': {'Label': _('New Records Only')} },
						'Typecast': GTypecast.text,
						'Default': 'Y' },
					'queryable': {
						'Description': 'Can records be queried?',
						'Label': _('Allow Querying'),
						'Typecast': GTypecast.boolean,
						'Default': True },
					'deletable': {
						'Description': 'Can records be deleted?',
						'Label': _('Allow Deletes'),
						'Typecast': GTypecast.boolean,
						'Default': True },
					'navigable': {
						'Description': 'Can this block be navigated?',
						'Label': _('Navigable'),
						'Typecast': GTypecast.boolean,
						'Default': True },
					'datasource': {
						'References': 'datasource.name',
						'Typecast': GTypecast.name,
						'Description': 'The name of a datasource (defined in by a '
						'{<datasource>} tag) that provides this block '
						'with it\'s data.' } },
				'ParentTags': ('logic',),
				'Label': _('Block'),
				'Description': 'A block contains instructions on how Forms '
				'should interact with a datasource.' },

			'label': {
				'BaseClass': GFObjects.GFLabel,
				'Attributes': {
					'name': {
						'Unique': True,
						'Typecast': GTypecast.name,
						'Description': _('The unique ID of the label.') },
					'text': {
						'Required': True,
						'Typecast': GTypecast.text,
						'Description': _('The text to be displayed.') },
					'for': {
						'References': 'entry.name',
						'Typecast': GTypecast.name,
						'Description': _('If this label is for a specific object, '
							'name it here.') },
					'alignment': {
						'Typecast': GTypecast.name,
						'ValueSet': {
							'left': {'Label': _('Left')},
							'right': {'Label': _('Right')},
							'center': {'Label': _('Centered')} },
						'Default': "left",
						'Description': 'The justification of the label. Can be one of '
						'the following: {left}, {right}, or {center}. '
						'Requires that the {width} attribute be set.'},
				},
				'Positionable': True,
				'ParentTags': ('layout','hbox','vbox','splitter','notepage','popupwindow','list'),
				'Label': _('Label'),
				'Description': 'Displays static text',
			},

			'field': {
				'BaseClass': GFObjects.GFField,
				'Importable': True,
				'Attributes': {
					'name': {
						'Required': True,
						'Unique': True,
						'Typecast': GTypecast.name,
						'Description': 'The unique ID of the entry. Referenced in '
						'master/detail setups as well as triggers.' },
					'description': {
						'Typecast': GTypecast.text,
						'Description': 'Text to display in a tooltip window'},
					'field': {
						'Typecast': GTypecast.name,
						'Label': _('Field (Database)'),
						'Description': 'The name of the field in the datasource to '
						'which this widget is tied.' },
					'datatype': {
						'Label': _("Datatype"),
						'Description': _("The type of data stored in this field."),
						'Typecast': GTypecast.name,
						'ValueSet': {
							'text':     {'Label': _("Text")},
							'number':   {'Label': _('Number')},
							'date':     {'Label': _("Date")},
							'time':     {'Label': _("Time")},
							'datetime': {'Label': _("Date and time")},
							'boolean':  {'Label': _('Boolean')},
							'array':    {'Label': _('Array')},
							'raw':      {'Label': _('Raw data')}},
						'Default': 'raw'},
					'itemtype': {
						'Label': _("Datatype"),
						'Description': _("The type of data stored in this field."),
						'Typecast': GTypecast.name,
						'ValueSet': {
							'text':     {'Label': _("Text")},
							'number':   {'Label': _('Number')},
							'date':     {'Label': _("Date")},
							'time':     {'Label': _("Time")},
							'datetime': {'Label': _("Date and time")},
							'boolean':  {'Label': _('Boolean')},
							'raw':      {'Label': _('Raw data')}},
						'Default': 'raw'},
					'length': {
						'Label': _("Length"),
						'Description': _(
							"Maximum length of data stored in this field. Applies "
							"only to fields with a datatype of 'string' or 'number'. "
							"For numbers, this is the total number of digits, "
							"including the fractional digits."),
						'Typecast': GTypecast.whole,
					},
					'scale': {
						'Label': _("Scale"),
						'Description': _(
							"Number of fractional digits. Applies only to fields with "
							"a datatype of 'number'."),
						'Typecast': GTypecast.whole,
						'Default': '0',},
					'groupDigits': {
						'Label': _("Group digits"),
						'Description': _(
							"If 'N', digits will not be grouped."),
						'Typecast': GTypecast.boolean,
						'Default': True},
					'case': {
						'Label': _("Case"),
						'Description': _(
							"Convert the value to uppercase/lowercase or leave it as "
							"it is. Applies only to fields with a datatype of "
							"'string'."),
						'Typecast': GTypecast.name,
						'ValueSet': {
							'mixed': {'Label': _('Mixed case')},
							'upper': {'Label': _('Upper case')},
							'lower': {'Label': _('Lower case')}},
						'Default': 'mixed'},
					'min': {
						'Label': _("Minimum"),
						'Description': _("Minimum value, value must be >= min"),
						'Typecast': GTypecast.text,
						'Default': 'None'},
					'max': {
						'Label': _("Maximum"),
						'Description': _("Maximum value, value must be <= max"),
						'Typecast': GTypecast.text,
						'Default': 'None'},
					'required': {
						'Label': _("Required"),
						'Description': _(
							"If set, empty values can not be stored in this field."),
						'Typecast': GTypecast.boolean,
						'Default': False},
					'maxLength': {
						'Typecast': GTypecast.whole,
						'Deprecated': 'Use length'},
					'minLength': {
						'Typecast': GTypecast.whole,
						'Label': _('Min Text Length'),
						'Description': 'The minimum number of characters the user must '
						'enter into the entry.',
						'Default': 0 },
					'max_length': {
						'Typecast': GTypecast.whole,
						'Deprecated': 'Use length',
						'Description': 'The maximum number of characters the user is '
						'allowed to enter into the entry.' },
					'min_length': {
						'Typecast': GTypecast.whole,
						'Deprecated': 'Use minLength',
						'Description': 'The minimum number of characters the user must '
						'enter into the entry.',
						'Default': 0 },
					'typecast': {
						'Typecast': GTypecast.name,
						'Deprecated': 'Use "type".'},
					'value': {
						'Typecast': GTypecast.text,
						'Deprecated': 'Use default="..." instead',
						'Description': 'Deprecated' },
					'fk_source': {
						'References': 'datasource.name',
						'Label': _('F/K Datasource'),
						'Typecast': GTypecast.name,
						'Description': 'Source table that the foreign key links to.' },
					'fk_key': {
						'Label': _('F/K Bound Field'),
						'Typecast': GTypecast.name,
						'Description': 'The table column (field) in the foreign key '
						'source table that the foreign key links to.' },
					'fk_description': {
						'Typecast': GTypecast.name,
						'Label': _('F/K Description Field'),
						'Description': 'The description used if a style of dropdown is '
						'selected. This field\'s value is displayed in '
						'the dropdown but the foreign_key value is '
						'actually stored in the field. This allows you '
						'to display something like the full name of a '
						'US state but only store it\'s 2 character '
						'abbreviation.' },
					'fk_resolved_description': {
						'Typecast': GTypecast.name,
						'Label': _('F/K Resolved Description Field'),
						'Description': 'Parent block field name '
						'containing fk_description for this row key.'},
					'fk_refresh': {
						'Typecast': GTypecast.name,
						'Label': _('F/K Refresh Method'),
						'ValueSet': {
							'never'   : {'Label': _('On form startup')},
							'startup' : {'Label': _('On form startup')},
							'activate': {'Label': _('On datasource activate')}
						#'change' : {'Label': _('On field modification')},
						#'commit' : {'Label': _('On commit')} },
						},
						'Default': 'startup',
						'Description': 'Decides when the foreign key should be '
						'refreshed.' },
					'default': {
						'Typecast': GTypecast.text,
						'Label': _('Default (New Records)'),
						'Description': 'The default value for this field when a new '
						'record is created. '
						'If the field is visible the user can override '
						'the value.' },
					'defaultToLast': {
						'Typecast': GTypecast.boolean,
						'Label': _('Default to last entry'),
						'Default': False,
						'Description': 'If {Y}, then new records will default to the '
						'last value the user entered for this field. If '
						'no new values have been entered, then defaults '
						'back to the normal {default} setting.' },
					'queryDefault':{
						'Typecast': GTypecast.text,
						'Label': _('Default (Querying)'),
						'Description': 'The field will be populated with this value '
						'automatically when a query is requested. If '
						'the field is visible the user can still '
						'override the value.' },
					'query_casesensitive': {
						'Typecast': GTypecast.boolean,
						'Label': _('Perform queries case-sensitive'),
						'Default': False,
						'Description': 'If "N", the entry widget ignores the case '
						'of the information entered into the query mask.'
					},
					'editable': {
						'Description': 'Only allow this object to be edited if it '
						'is currently empty.',
						'Label': _('Allow Editing'),
						'ValueSet': {
							'Y': {'Label': _('Yes')},
							'N': {'Label': _('No')},
							#'null': {'Label': _('Null Only')},
							'update': {'Label': _('Update Only')},
							'new': {'Label': _('New Records Only')} },
						'Typecast': GTypecast.text,
						'Default': 'Y' },
					'queryable': {
						'Description': 'Is this object queryable?',
						'Label': _('Allow Query'),
						'Typecast': GTypecast.boolean,
						'Default': True },
					'autoquery': {
						'Description': 'If {Y} then any changes in this field will '
						'cause the form to automatically query and '
						'populate itself with matching records.  If '
						'{New} it will only automatically query if '
						'the form is currenly completely empty.  If '
						'{N} then no automatic query will be performed.',
						'Label': _('Automatic Query'),
						'ValueSet': {
							'Y': {'Label': _('Yes')},
							'N': {'Label': _('No')},
							'new': {'Label': _('Empty forms only')} },
						'Typecast': GTypecast.text,
						'Default': 'N' },
					'ltrim': {
						'Label': _('Trim left spaces'),
						'Description': 'Trim extraneous space at '
						'beginning of user input.',
						'Typecast': GTypecast.boolean,
						'Default': False },
					'rtrim': {
						'Label': _('Trim right spaces'),
						'Description': 'Trim extraneous space at end '
						'of user input.',
						'Typecast': GTypecast.boolean,
						'Default': True },
					'disableAutoCompletion': {
						'Typecast': GTypecast.boolean,
						'Label': _('Disable auto completion'),
						'Description': 'Disable auto completion',
						'Default': False },
					'inputmask': {
						'Typecast': GTypecast.text,
						'Label': _('Input Mask'),
						'Description': 'Defines how the user will edit a field\'s '
						'value.' } },
				'ParentTags': ('block',),
				'Label': _('Field'),
				'Description': 'A field represents a column in the database table '
				'designated by the block.' },

			'entry': {
				'BaseClass': GFObjects.GFEntry,
				'Attributes': {
					'name': {
						'Unique': True,
						'Typecast': GTypecast.name,
						'Description': 'The unique ID of the entry.' },
					'label': {
						'Typecast': GTypecast.text,
						'Description': 'The optional label displayed next to checkbox.' },
					'description': {
						'Typecast': GTypecast.text,
						'Description': 'Text to display in a tooltip window' },
					'field': {
						'Typecast': GTypecast.name,
						'References': 'field.name',
						'Required': True,
						'Description': 'The name of the field that this ties to.' },
					'block': {
						'Typecast': GTypecast.name,
						'References': 'block.name',
						'Description': 'The name of the block that this ties to.' },
					'focusorder': {
						'Typecast': GTypecast.whole,
						'Label': _('Focus Order'),
						'Description': 'Defines what order the focus moves through '
						'entries.'},
					'navigable': {
						'Typecast': GTypecast.boolean,
						'Description': 'If false, the user will be unable to navigate '
						'to this entry. Triggers can still '
						'alter the value though.',
						'Default': True   },
					'visible': {
						'Typecast': GTypecast.boolean,
						'Default': True,
						'Deprecated': 'Is entry visible'},
					'style': {
						'Typecast': GTypecast.name,
						'ValueSet': {
							'auto'       : {'Label': _('Automatic')},
							'default'    : {'Label': _('Default')},
							'text'       : {'Label': _('Text Field')},
							'multiline'  : {'Label': _('Multiline-Edit')},
							'password'   : {'Label': _('Password/Hidden')},
							'dropdown'   : {'Label': _('Dropdown/Combo box')},
							'listbox'    : {'Label': _('Listbox')},
							'radiobox'   : {'Label': _('Radio box')},
							'radiobutton': {'Label': _('Radio button')},
							'checkbox'   : {'Label': _('Checkbox')},
							'bitcheckbox': {'Label': _('Checkbox bound to bit field')},
							'datepicker' : {'Label': _('Date picker')},
							'picker'     : {'Label': _('User defined picker')},
							'picker_with_editor' : {'Label': _('User defined picker with custom editor buton')},
							'text_with_buttons' : {'Label': _('Text field with buttons')},
							'label'      : {'Label': _('Label (non-editable)')},
						},
						'Default': 'auto',
						'Description': 'The style of entry widget requested. '
						'Currently either {text}, {label}, {checkbox}, '
						'{listbox}, or {dropdown}. To use {listbox} or '
						'{dropdown} you are required to use both the '
						'{fk_source}, {fk_key}, and {fk_description} '
						'attributes. The {label} style implies the '
						'{readonly} attribute.'  },

					'maxitems': {
						'Typecast': GTypecast.whole,
						'Default': 2,
						'Label': _('Max item count'),
						'Description': 'For radiobox style only.'
						'Because max item count is static' },

					'activate_value': {
						'Typecast': GTypecast.text,
						'Label': _('Value this entry sets when activated'),
						'Description': 'For radiobutton style only.'},

					'picker_text_minlength': {
						'Typecast': GTypecast.integer,
						'Default': '-1',
						'Label': _('Number of characters to popup picker'),
						'Description': 'For picker* styles only'},

					'formatmask': {
						'Typecast': GTypecast.text,
						'Label': _('Format Mask'),
						'Description': 'TODO' },
					'inputmask': {
						'Typecast': GTypecast.text,
						'Label': _('Input Mask'),
						'Description': 'Defines how the user will edit a field\'s '
						'value.' },
					'displaymask': {
						'Label': _('Display Mask'),
						'Typecast': GTypecast.text,
						'Description': 'Defines how the field data will be formatted '
						'for display.' } },
				'Positionable': True,
				'ParentTags': ('layout','hbox','vbox','table','splitter','notepage','popupwindow','list'),
				'Label': _('Entry'),
				'Description': 'An {entry} is the visual counterpart to a {field}, '
				'it defines how the data in a field will be displayed '
				'and how it can be edited.'},

			'popupwindow': {
				'BaseClass': GFObjects.GFPopupWindow,
				'Importable': True,
				'Attributes': {
					'name': {
						'Unique': True,
						'Typecast': GTypecast.name,
						'Description': 'The unique ID of the object' },
					'title': {
						'Typecast': GTypecast.text,
						'Description': 'Window title optional' },
					'modal': {
						'Typecast': GTypecast.boolean,
						'Default': 'N',
						'Description': 'Modal or not' },
					'form': {
						'Typecast': GTypecast.name,
						'Description': 'Form definition name to show in' },
					'parameters': {
						'Typecast': GTypecast.expression,
						'Description': 'Form parameters' },
					'popupReadonly': {
						'Typecast': GTypecast.boolean,
						'Default': 'N',
						'Description': 'popup button enabled even in readonly' },
				},
				'ParentTags': ('entry',),
				'Label': _('Generic popup window'),
				'Description': 'Custom popup window, container for widgets',
			},

			'vbox': {
				'BaseClass': GFObjects.GFVBox,
				'Attributes': {
					'name': {
						'Unique': True,
						'Typecast': GTypecast.name,
						'Description': 'The unique name of the box.' },
					'label': {
						'Typecast': GTypecast.text,
						'Description': 'An optional text label that will be displayed '
						'on the border.' },
					'block': {
						'Typecast': GTypecast.name,
						'References': 'block.name',
						'Description': 'The {block}' }},
				'Positionable': True,
				'ParentTags': ('layout','vbox','hbox','splitter','notepage','popupwindow','list','treelist'),
				'Label': _('Box (Vertical)'),
				'Description': 'A box is a visual element that draws a box around '
				'other visual elements, thus providing logical '
				'separation for them.' },
			'hbox': {
				'BaseClass': GFObjects.GFHBox,
				'Attributes': {
					'name': {
						'Unique': True,
						'Typecast': GTypecast.name,
						'Description': 'The unique name of the box.' },
					'label': {
						'Typecast': GTypecast.text,
						'Description': 'An optional text label that will be displayed '
						'on the border.' },
					'block': {
						'Typecast': GTypecast.name,
						'References': 'block.name',
						'Description': 'The {block}' }},
				'Positionable': True,
				'ParentTags': ('layout','vbox','hbox','splitter','notepage','popupwindow','list','treelist'),
				'Label': _('Box (Horizontal)'),
				'Description': 'A box is a visual element that draws a box around '
				'other visual elements, thus providing logical '
				'separation for them.' },

			'image': {
				'BaseClass': GFObjects.GFImage,
				'Attributes': {
					'name': {
						'Unique': True,
						'Typecast': GTypecast.name,
						'Description': 'The unique name of the image.' },
					'field': {
						'Typecast': GTypecast.name,
						'References': 'field.name',
						'Required': True,
						'Description': 'The name of the field that this ties to.' },
					'block': {
						'Typecast': GTypecast.name,
						'References': 'block.name',
						'Description': 'The name of the block that this ties to.' },
					'type':        {
						'Typecast': GTypecast.name,
						'ValueSet': {
							'URL': {'Label': _('Field contains the URL of the image')},
							'PIL': {'Label': _('Field contains a PIL encoding of the image')} },
						'Default': "URL",
						'Description': 'The type of image reference. Can be {URL} '
						'for a url reference, or {PIL} for an '
						'embedded image.' },
					'fit':  {
						'Typecast': GTypecast.name,
						'ValueSet': {
							'none': {'Label': _('Full-size image (no scaling)')},
							'width': {'Label': _('Scale to width')},
							'height': {'Label': _('Scale to height')},
							'both': {'Label': _('Scale width and height (may distort image)')},
							'auto': {'Label': _('Use a best-fit algorithm')} },
						'Default': "none",
						'Description': 'Defines how the image will fill the space '
						'provided for it (crop parts outside borders, '
						'or stretch width/height/both to fit into '
						'given boundaries).' },
					'label': {
						'Typecast': GTypecast.text,
						'Description': 'Label displayed next or above to the image' },
					'focusorder': {
						'Typecast': GTypecast.whole,
						'Description': 'Defines what order the focus moves through '
						'entries.'  } },
				'Positionable': True,
				'ParentTags': ('layout','vbox','hbox','table','splitter','notepage','popupwindow','list'),
				'Label': _('Image'),
				'Description': 'Displays an image.' },

			'component': {
				'BaseClass': GFObjects.GFComponent,
				'Attributes': {
					'name': {
						'Unique': True,
						'Typecast': GTypecast.name,
						'Description': 'The unique name of the component.' },
					'field': {
						'Typecast': GTypecast.name,
						'References': 'block.name>field.name',
						'Required': True,
						'Description': 'The name of the field that this ties to.' },
					'block': {
						'Typecast': GTypecast.name,
						'References': 'block.name',
						'Required': True,
						'Description': 'The name of the block that this ties to.' },
					'mimetype':        {
						'Typecast': GTypecast.name,
						'Required': True,
						'Description': 'TODO' },
					'type':        {
						'Typecast': GTypecast.name,
						'ValueSet': {
							'URL': {'Label': _('Field contains the URL of the component')},
							'Base64': {'Label': _("Field contains the data of the "
									"component in Base64 encoding")} },
						'Default': "URL",
						'Description': 'TODO' },
					'focusorder': {
						'Typecast': GTypecast.whole,
						'Description': 'Defines what order the focus moves through '
						'entries.'  } },
				'Positionable': True,
				'ParentTags': ('layout','vbox','hbox'),
				'Label': _('Embedded Component'),
				'Description': 'TODO' },

			'url-resource': {
				'BaseClass': GFObjects.GFUrlResource,
				'Attributes': {
					'name': {
						'Unique': True,
						'Typecast': GTypecast.name,
						'Description': 'The unique name of the component' },
					'label': {
						'Typecast': GTypecast.text,
						'Description': 'The optional label' },
					'field': {
						'Typecast': GTypecast.name,
						'References': 'block.name>field.name',
						'Required': True,
						'Description': 'The name of the field that this ties to.' },
					'block': {
						'Typecast': GTypecast.name,
						'References': 'block.name',
						'Description': 'The name of the block that this ties to.' },
					'content_type': {
						'Typecast': GTypecast.text,
						'Default': '*/*',
						'Description': 'The content-type of url resource',
					},
				},
				'Positionable': True,
				'ParentTags': ('layout','vbox','hbox','table','splitter','notepage','popupwindow','list'),
				'Description': 'Url browser' },

			'button': {
				'BaseClass': GFObjects.GFButton,
				'Importable': True,
				'Attributes': {
					'name': {
						'Unique': True,
						'Typecast': GTypecast.name,
						'Description': 'A unique ID for the widget. Useful for '
						'importable buttons. ' },
					'navigable': {
						'Description': 'Can this button be navigated?',
						'Label': _('Navigable'),
						'Typecast': GTypecast.boolean,
						'Default': True },
					'enabled': {
						'Description': 'Is this button enabled',
						'Label': _('Enabled'),
						'Typecast': GTypecast.boolean,
						'Default': True },
					'default': {
						'Description': 'Is this button default?',
						'Label': _('Default'),
						'Typecast': GTypecast.boolean,
						'Default': False },
					'block': {
						'Typecast': GTypecast.name,
						'References': 'block.name',
						'Description': 'The (optional) name of the block that this '
						'ties to. If a button is associated with '
						'a block, then the button honors '
						'the block\'s rows= value.' },
					'focusorder': {
						'Typecast': GTypecast.whole,
						'Description': 'Defines what order the focus moves through '
						'entries.'},
					'label': {
						'Typecast': GTypecast.name,
						'Description': 'The text that should appear on the button' },
					'description': {
						'Label'      : _("Description"),
						'Description': _("Text to display in a tooltip window"),
						'Typecast'   : GTypecast.text},
					'image': {
						'Typecast': GTypecast.text,
						'Description': 'Path to image that should appear on the button' },
					'imagemask': {
						'Typecast': GTypecast.color,
						'Description': 'Mask color for image' },
					'action': {
						'Typecast': GTypecast.name,
						'Description': 'Action to be executed when the button is fired'}},
				'Positionable': True,
				'ParentTags': ('layout','vbox','hbox','table','splitter','notepage','popupwindow','list'),
				'Label': _('Button'),
				'Description': 'A visual element with text placed on it, that '
				'the user can push or click, and that event can run '
				'a bound trigger.' },

			'entry-button': {
				'BaseClass': GFObjects.GFEntryButton,
				'Importable': True,
				'Attributes': {
					'name': {
						'Unique': True,
						'Typecast': GTypecast.name,
						'Description': 'A unique ID for the widget. Useful for '
						'importable buttons. ' },
					'enabled': {
						'Description': 'Is this button enabled',
						'Label': _('Enabled'),
						'Typecast': GTypecast.boolean,
						'Default': True },
					'label': {
						'Typecast': GTypecast.name,
						'Description': 'The text that should appear on the button' },
					'image': {
						'Typecast': GTypecast.text,
						'Description': 'Path to image that should appear on the button' },
					'imagemask': {
						'Typecast': GTypecast.color,
						'Description': 'Mask color for image' },
					'action': {
						'Typecast': GTypecast.name,
						'Description': 'Action to be executed when the button is fired'}},
				'Positionable': True,
				'ParentTags': ('entry',),
				'Label': _('Entry button'),
				'Description': 'A visual element with text placed on it, that '
				'the user can push or click, and that event can run '
				'a bound trigger. Placed inside of entry.' },

			'table' : {
				'BaseClass' : GFObjects.GFTable,
				'Importable': True,
				'Attributes' : {
					'name' : {
						'Unique' : True,
						'Typecast' : GTypecast.name,
						'Description' : 'Unique name of the object'},
					'label': {
						'Typecast': GTypecast.text,
						'Description': 'The optional label displayed next to checkbox.',
					},
					'block' : {
						'Typecast' : GTypecast.name,
						'Description' : 'The block that provides data for this table'},
					'fld_style' : {
						'Label' : _('Field with style list'),
						'Typecast' : GTypecast.text,
						'Description' : _('Field with style list')},
					'selectionMode' : {
						'Typecast' : GTypecast.name,
						'Description' : 'How table selects content',
						'ValueSet': {
							'cells'   : { 'Label': _('Select cells')   },
							'rows'    : { 'Label': _('Select rows')    },
							'columns' : { 'Label': _('Select columns') },
						},
						'Default': "cells",
					},
					'rowCount' : {
						'Typecast' : GTypecast.whole,
						'Description' : 'Number of row to be visible (to calculate best size)',
						'Default': "2",
					},
				},
				'ParentTags' : ('layout','hbox','vbox','splitter','notepage','popupwindow','list'),
				'Label' : _('Table'),
				'Description' : _('The table component with cell renderers, entries used for data editing')},

			'table-row-styles' : {
				'BaseClass' : GFObjects.GFStyles,
				'Importable': True,
				'Attributes' : {
					'name' : {
						'Unique' : True,
						'Typecast' : GTypecast.name,
						'Description' : _('Unique name of the object')},
				},
				'Positionable' : True,
				'ParentTags' : ('table',),
				'Description' : _('Table row styles'),
			},
			'table-row-style' : {
				'BaseClass' : GFObjects.GFTableRowStyle,
				'Attributes' : {
					'name' : {
						'Label' : _('Name'),
						'Unique' : True,
						'Typecast' : GTypecast.name,
						'Description' : _('Unique name of the object'),
					},
					#'bold' : {
					#	'Label' : _('Bold'),
					#	'Typecast' : GTypecast.boolean,
					#	'Description' : _('Is tree node text bold'),
					#},
					#'italic' : {
					#	'Label' : _('Italic'),
					#	'Typecast' : GTypecast.boolean,
					#	'Description' : _('Is tree node text italic'),
					#},
					'textcolor' : {
						'Label' : _('Text color'),
						'Typecast' : GTypecast.color,
					},
					'bgcolor' : {
						'Label' : _('Background color'),
						'Typecast' : GTypecast.color,
					},
				},
				'Positionable' : True,
				'ParentTags' : ('table-row-styles',),
				'Description' : 'Tree node style',
			},

			'list' : {
				'BaseClass' : GFObjects.GFList,
				'Importable': True,
				'Attributes' : {
					'name' : {
						'Unique' : True,
						'Typecast' : GTypecast.name,
						'Description' : 'Unique name of the object'},
					'block' : {
						'Typecast' : GTypecast.name,
						'Description' : 'The block that provides data for this table'},
					'itemname' : {
						'Label' : _('Item name pattern'),
						'Typecast' : GTypecast.text,
						'Description' : 'Item name pattern. Use "%(field)s" to reference field'},
					'style': {
						'Typecast': GTypecast.name,
						'Label': _('Style'),
						'ValueSet': {
							'buttons': {'Label': _('Button list')},
							'tabs'   : {'Label': _('Tabbed')} },
						'Default': 'buttons',
						'Description': _('List gui implementation'),
					},
				},
				'ParentTags' : ('layout','hbox','vbox','splitter','notepage','popupwindow','list'),
				'Label' : _('Table'),
				'Description' : _('The table component with cell renderers, entries used for data editing')},

			'total' : {
				'BaseClass' : GFObjects.GFTotal,
				'MixedContent'   : True,
				'KeepWhitespace' : True,
				'Description' : _('Updates parent field with total value of the source column'),
				'Attributes' : {
					'name' : {
						'Unique' : True,
						'Typecast' : GTypecast.name,
						'Description' : 'Unique name of the object'},
					'source' : {
						'Typecast' : GTypecast.name,
						'Required' : True,
						'Description' : 'Source block and field, dot separated'},
					'function' : {
						'Typecast' : GTypecast.name,
						'Description' : 'Function used to calculate total',
						'ValueSet': {
							'sum'  : { 'Label': _('Sum') },
							'min'  : { 'Label': _('Minimum') },
							'max'  : { 'Label': _('Maximum') },
							'count': { 'Label': _('Count') },
						},
						'Default': "sum",
					},
					'language': {
						'Label'      : _("Language"),
						'Description': _("Programming language the code is written in"),
						'Typecast'   : GTypecast.name,
						'Default'    : 'python',
						'ValueSet'   : {
							'python': {'Label': "Python"},
						},
					},
				},
				'ParentTags' : ('field',),
			},

			'calc' : {
				'BaseClass'      : GFObjects.GFCalc,
				'Description'    : _("Automatically updates parent field value with calculated one. Listens for all source fields changes"),
				'MixedContent'   : True,
				'KeepWhitespace' : True,
				'Attributes' : {
					'name' : {
						'Unique' : True,
						'Typecast' : GTypecast.name,
						'Description' : 'Unique name of the object'
					},
					'language': {
						'Label'      : _("Language"),
						'Description': _("Programming language the code is written in"),
						'Typecast'   : GTypecast.name,
						'Default'    : 'python',
						'ValueSet'   : {
							'python': {'Label': "Python"},
						},
					},
				},
				'ParentTags' : ('field',),
			},

			'timer' : {
				'BaseClass'      : GFObjects.GFTimer,
				'Description'    : _("Runs user code on timer"),
				'MixedContent'   : True,
				'KeepWhitespace' : True,
				'Attributes' : {
					'name' : {
						'Unique' : True,
						'Typecast' : GTypecast.name,
						'Description' : 'Unique name of the object'
					},
					'language': {
						'Label'      : _("Language"),
						'Description': _("Programming language the code is written in"),
						'Typecast'   : GTypecast.name,
						'Default'    : 'python',
						'ValueSet'   : {
							'python': {'Label': "Python"},
						},
					},
					'time' : {
						'Required' : True,
						'Typecast' : GTypecast.whole,
						'Description' : 'Time to repeat',
					},
					'oneshot' : {
						'Typecast' : GTypecast.boolean,
						'Default'  : 'N',
						'Description' : 'Time to repeat',
					},
					'autostart' : {
						'Typecast' : GTypecast.boolean,
						'Default'  : 'Y',
						'Description' : 'If starts automatically',
					},
				},
				'ParentTags' : ('form','dialog'),
			},

			'tree' : {
				# TODO: uncomment required tags and fix importable with required tags
				'BaseClass' : GFObjects.GFTree,
				'Importable': True,
				'Attributes' : {
					'name' : {
						'Unique' : True,
						'Typecast' : GTypecast.name,
						'Description' : 'Unique name of the object'},
					'label': {
						'Typecast': GTypecast.text,
						'Description': 'The optional label displayed next to checkbox.',
					},
					'block' : {
						'Typecast' : GTypecast.name,
						'References' : 'block.name',
						#'Required' : True,
						'Description' : 'The name of the block the tree ties to'},
					'fld_id' : {
						'Label' : _('Own ID field'),
						'Typecast' : GTypecast.name,
						#'Required' : True,
						'Description' : 'The field containing tree node id'},
					'fld_parent' : {
						'Label' : _('Parent ID field'),
						'Typecast' : GTypecast.name,
						#'Required' : True,
						'Description' : 'The field containing tree node parent'},
					'fld_style' : {
						'Label' : _('Style name'),
						'Typecast' : GTypecast.text,
						'Description' : 'Node style name'},
					'nodename' : {
						'Label' : _('Tree node name pattern'),
						'Typecast' : GTypecast.name,
						#'Required' : True,
						'Description' : 'Tree node name pattern. Use "%(field)s" to reference field'},
					'rootid' : {
						'Label' : _('Root id'),
						'Typecast' : GTypecast.text,
						'Description' : 'Root id, default is 0',
						'Default' : '0'},
					'rootname' : {
						'Label' : _('Root name'),
						'Typecast' : GTypecast.text,
						'Description' : 'Root name, if tree has virtual root'},
					'expanded' : {
						'Typecast' : GTypecast.boolean,
						'Default' : 'N',
						'Description' : 'Is tree expanded'},
					'checkable' : {
						'Typecast' : GTypecast.boolean,
						'Default' : 'N',
						'Description' : 'If all tree nodes checkable'},
					'autocheck' : {
						'Typecast' : GTypecast.boolean,
						'Default' : 'Y',
						'Description' : 'Auto check parent, auto check child'},
					'labelEdit' : {
						'Typecast' : GTypecast.boolean,
						'Default' : 'Y',
						'Description' : 'Is tree labels editable'},
					'navigable': {
						'Typecast': GTypecast.boolean,
						'Description': 'If false, the user will be unable to navigate '
						'to this entry. Triggers can still '
						'alter the value though.',
						'Default': True   },
					'deleteMessage' : {
						'Typecast': GTypecast.text,
						'Description': 'Additional message to show when deleting node',
						'Default': '' },
				},
				'Positionable' : True,
				'ParentTags' : ('layout','hbox','vbox','splitter','notepage','popupwindow','list'),
				'Description' : _('Tree-View of a block'),
			},
			'treelist' : {
				# NOTE: tree without 
				#	nodename
				#	labelEdit
				#	navigable
				#
				# TODO: uncomment required tags and fix importable with required tags
				'BaseClass' : GFObjects.GFTreeList,
				'Importable': True,
				'Attributes' : {
					'name' : {
						'Unique' : True,
						'Typecast' : GTypecast.name,
						'Description' : 'Unique name of the object'},
					'label': {
						'Typecast': GTypecast.text,
						'Description': 'The optional label',
					},
					'block' : {
						'Typecast' : GTypecast.name,
						'References' : 'block.name',
						#'Required' : True,
						'Description' : 'The name of the block the component ties to'},
					'fld_id' : {
						'Label' : _('Own ID field'),
						'Typecast' : GTypecast.name,
						#'Required' : True,
						'Description' : 'The field containing tree node id'},
					'fld_parent' : {
						'Label' : _('Parent ID field'),
						'Typecast' : GTypecast.name,
						#'Required' : True,
						'Description' : 'The field containing tree node parent'},
					'fld_style' : {
						'Label' : _('Style name'),
						'Typecast' : GTypecast.text,
						'Description' : 'Node style name'},
					'nodename' : {
						'Label' : _('Tree node name pattern'),
						'Typecast' : GTypecast.name,
						#'Required' : True,
						'Description' : 'Tree node name pattern. Use "%(field)s" to reference field'},
					'rootid' : {
						'Label' : _('Root id'),
						'Typecast' : GTypecast.text,
						'Description' : 'Root id, default is 0',
						'Default' : '0'},
					'rootname' : {
						'Label' : _('Root name'),
						'Typecast' : GTypecast.text,
						'Description' : 'Root name, if tree has virtual root'},
					'expanded' : {
						'Typecast' : GTypecast.boolean,
						'Default' : 'N',
						'Description' : 'Is tree expanded'},
					'deleteMessage' : {
						'Typecast': GTypecast.text,
						'Description': 'Additional message to show when deleting node',
						'Default': '' },
				},
				'Positionable' : True,
				'ParentTags' : ('layout','hbox','vbox','splitter','notepage','popupwindow','list'),
				'Description' : _('Tree-View of a block'),
			},
			'treenode-styles' : {
				'BaseClass' : GFObjects.GFStyles,
				'Importable': True,
				'Attributes' : {
					'name' : {
						'Unique' : True,
						'Typecast' : GTypecast.name,
						'Description' : _('Unique name of the object')},
				},
				'Positionable' : True,
				'ParentTags' : ('tree', 'treelist'),
				'Description' : _('Tree node style'),
			},
			'treenode-style' : {
				'BaseClass' : GFObjects.GFTreeNodeStyle,
				'Attributes' : {
					'name' : {
						'Label' : _('Name'),
						'Unique' : True,
						'Typecast' : GTypecast.name,
						'Description' : _('Unique name of the object'),
					},
					'icon' : {
						'Label' : _('Icon'),
						'Typecast' : GTypecast.text,
						'Description' : _('Tree node icon name'),
					},
					'button' : {
						'Label' : _('Button'),
						'Typecast': GTypecast.name,
						'Description' : _('Tree node kind'),
						'ValueSet': {
							'checkbox' : {'Label': _('Node with checkbox')},
							'radiobox' : {'Label': _('Node with radiobox')},
						},
						'Description' : _('Kind of button with this node'),
					},
					'checked' : {
						'Label' : _('Checked'),
						'Typecast' : GTypecast.boolean,
						'Description' : _('Is tree node initially checked'),
					},
					'bold' : {
						'Label' : _('Bold'),
						'Typecast' : GTypecast.boolean,
						'Description' : _('Is tree node text bold'),
					},
					'italic' : {
						'Label' : _('Italic'),
						'Typecast' : GTypecast.boolean,
						'Description' : _('Is tree node text italic'),
					},
					'expanded' : {
						'Label' : _('Expanded'),
						'Typecast' : GTypecast.boolean,
						'Description' : _('Is tree node expanded'),
					},
					'textcolor' : {
						'Label' : _('Text color'),
						'Typecast' : GTypecast.color,
					},
					'bgcolor' : {
						'Label' : _('Background color'),
						'Typecast' : GTypecast.color,
					},
					'flags' : {
						'Label' : _('Columns flags'),
						'Typecast' : GTypecast.names,
						'Default' : '',
					},
				},
				'Positionable' : True,
				'ParentTags' : ('treenode-styles',),
				'Description' : 'Tree node style',
			},
			'tree-columns' : {
				'BaseClass' : GFObjects.GFObj,
				'Importable': True,
				'Attributes' : {
					'name' : {
						'Unique' : True,
						'Typecast' : GTypecast.name,
						'Description' : 'Unique name of the object'},
				},
				'Positionable' : True,
				'ParentTags' : ('tree',),
				'Description' : 'Tree columns',
			},
			'tree-column' : {
				'BaseClass' : GFObjects.GFTreeColumn,
				'Attributes' : {
					'name' : {
						'Label' : _('Name'),
						'Unique' : True,
						'Typecast' : GTypecast.name,
						'Description' : _('Unique name of the object'),
					},
					'width' : {
						'Label' : _('Column width'),
						'Typecast' : GTypecast.whole,
						'Default' : '24',
					},
					'icon' : {
						'Typecast' : GTypecast.text,
						'Description' : _('Column true icon name'),
					},
					'icon_off' : {
						'Typecast' : GTypecast.text,
						'Description' : _('Column false icon name'),
					},
					'icon_description' : {
						'Typecast' : GTypecast.text,
						'Description' : _('Column true icon description'),
					},
					'icon_off_description' : {
						'Typecast' : GTypecast.text,
						'Description' : _('Column false icon description'),
					},
				},
				'Positionable' : True,
				'ParentTags' : ('tree-columns',),
				'Description' : _('Tree column'),
			},
			'dyn-menu' : {
				'BaseClass' : GFObjects.GFDynMenu,
				'Attributes' : {
					'name' : {
						'Unique'      : True,
						'Typecast'    : GTypecast.name,
						'Description' : 'Unique name of the menu'},
					'label': {
						'Label'       : _("Label"),
						'Description' : _("Text to use if this is a submenu"),
						'Typecast'    : GTypecast.text},
					'block' : {
						'Typecast'    : GTypecast.name,
						'References'  : 'block.name',
						'Description' : 'The name of the block the menu ties to.'},
					'fld_id' : {
						'Label'       : _('Own ID field'),
						'Typecast'    : GTypecast.name,
						'Required'    : True,
						'Description' : 'The field containing the TreeViewItem ID'},
					'fld_parent' : {
						'Label'       : _('Parent ID field'),
						'Typecast'    : GTypecast.name,
						'Required'    : True,
						'Description' : 'The field containing the TreeViewItem parent'},
					'nodename' : {
						'Label'       : _('Menu node name pattern'),
						'Typecast'    : GTypecast.name,
						'Required'    : True,
						'Description' : 'Menu node name pattern. Use %(field) to reference field'},
					'rootid' : {
						'Label'       : _('Root id'),
						'Typecast'    : GTypecast.name,
						'Description' : 'Root id, default is 0',
						'Default'     : '0'},
				},
				'Positionable' : True,
				'ParentTags'   : ('menu','button'),
				'Description'  : 'Menu-View of a blcok',
			},

			'gant' : {
				'BaseClass' : GFObjects.GFGant,
				'Attributes' : {
					'name' : {
						'Unique' : True,
						'Typecast' : GTypecast.name,
						'Description' : _('Unique name of the object')},
					'block_activity' : {
						'Typecast' : GTypecast.name,
						'References' : 'block.name',
						'Required' : True,
						'Description' : _('The name of the block the gant ties activity to')},
					'fld_id' : {
						'Label' : _('Activity id field'),
						'Typecast' : GTypecast.name,
						'Required' : True,
						'Description' : _('Activity index field')},
					'fld_row' : {
						'Label' : _('Activity row field'),
						'Typecast' : GTypecast.name,
						'Required' : True,
						'Description' : _('Activity row field')},
					'fld_name' : {
						'Label' : _('Activity name field'),
						'Typecast' : GTypecast.name,
						'Required' : True,
						'Description' : _('Activity name field')},
					'fld_duration' : {
						'Label' : _('Activity duration field'),
						'Typecast' : GTypecast.name,
						'Required' : True,
						'Description' : _('Activity duration field')},
					'fld_start_min' : {
						'Label' : _('Activity minimal start time field'),
						'Typecast' : GTypecast.name,
						'Required' : False,
						'Description' : _('Activity minimal start time field')},
					'fld_start' : {
						'Label' : _('Activity start time field'),
						'Typecast' : GTypecast.name,
						'Required' : False,
						'Description' : _('Activity start time field, calculated by gant diagram model')},

					'block_precedence' : {
						'Typecast' : GTypecast.name,
						'References' : 'block.name',
						'Required' : True,
						'Description' : _('The name of the block the gant ties precedende to')},
					'fld_activity_from' : {
						'Label' : _('Precedence activity id'),
						'Typecast' : GTypecast.name,
						'Required' : True,
						'Description' : _('Precedence activity id')},
					'fld_activity_to' : {
						'Label' : _('Subsequent activity id'),
						'Typecast' : GTypecast.name,
						'Required' : True,
						'Description' : _('Activity start time field')},
					'fld_lag' : {
						'Label' : _('Link lag'),
						'Typecast' : GTypecast.name,
						'Required' : False,
						'Description' : _('Link lag')},
					
					'navigable': {
						'Typecast': GTypecast.boolean,
						'Description': 'If false, the user will be unable to navigate '
						'to this entry. Triggers can still '
						'alter the value though.',
						'Default': True   },
				},
				'Positionable' : True,
				'ParentTags' : ('layout','hbox','vbox','splitter','notepage','popupwindow','list'),
				'Description' : _('Gantt diagram'),
			},

			'calendar' : {
				'BaseClass' : GFObjects.GFCalendar,
				'Importable' : True,
				'Attributes' : {
					'name' : {
						'Unique' : True,
						'Typecast' : GTypecast.name,
						'Description' : _('Unique name of the object')},

					'block' : {
						'Typecast' : GTypecast.name,
						'References' : 'block.name',
						#'Required' : True,
						'Description' : _('The name of the block the gant ties activity to')},
					'fld_date' : {
						'Label' : _('Date field'),
						'Typecast' : GTypecast.name,
						#'Required' : True,
						'Description' : _('Date field name')},
					'fld_daytype_id' : {
						'Label' : _('Day type field'),
						'Typecast' : GTypecast.name,
						#'Required' : True,
						'Description' : _('Day type field name')},
					'fld_daytype_description' : {
						'Label' : _('Day type description field'),
						'Typecast' : GTypecast.name,
						#'Required' : True,
						'Description' : _('Day type description field name')},
					'fld_daytype_params' : {
						'Label' : _('Day type params field'),
						'Typecast' : GTypecast.name,
						#'Required' : True,
						'Description' : _('Day type params field name')},

					'navigable': {
						'Typecast': GTypecast.boolean,
						'Description': 'If false, the user will be unable to navigate '
						'to this entry. Triggers can still '
						'alter the value though.',
						'Default': True   },
				},
				'Positionable' : True,
				'ParentTags' : ('layout','hbox','vbox','splitter','notepage','popupwindow','list'),
				'Description' : _('Calendar diagram'),
			},

			'mdi-notebook' : {
				'BaseClass' : GFObjects.GFMDINotebook,
				'Attributes' : {
					'name' : {
						'Unique' : True,
						'Typecast' : GTypecast.name,
						'Description' : 'Unique name of the notebook'},
					'max_title_length': {
						'Typecast': GTypecast.whole,
						'Description': 'Max chars in title'},
					'closable': {
						'Typecast': GTypecast.boolean,
						'Description': 'If user can close pages',
						'Default': True   },
				},
				'Positionable' : True,
				'ParentTags' : ('layout','hbox','vbox','splitter','notepage','popupwindow','list'),
				'Description' : 'MDI Notebook, opens forms',
			},

			'notebook' : {
				'BaseClass' : GFObjects.GFNotebook,
				'Importable' : True,
				'Attributes' : {
					'name' : {
						'Unique' : True,
						'Typecast' : GTypecast.name,
						'Description' : 'Unique name of the notebook'},
				},
				'Positionable' : True,
				'ParentTags' : ('layout','hbox','vbox','splitter','notepage','popupwindow','list'),
				'Description' : 'Container widget with a tabbar, allows to switch between contained components',
			},

			'notepage' : {
				'BaseClass' : GFObjects.GFNotepage,
				'Importable' : True,
				'Attributes' : {
					'name' : {
						'Unique' : True,
						'Typecast' : GTypecast.name,
						'Description' : 'Unique name of the page'},
					'caption' : {
						'Unique' : True,
						'Typecast' : GTypecast.text,
						'Default': 'Untitled',
						'Description' : 'Title of a page'},
					'description': {
						'Label'      : _("Description"),
						'Description': _("Text to display in a tooltip"),
						'Typecast'   : GTypecast.text,
					},
					'icon' : {
						'Typecast' : GTypecast.text,
						'Description' : 'Icon'},
				},
				'Positionable' : True,
				'ParentTags' : ('notebook',),
				'Description' : 'Page of notebook, container',
			},

			'splitter' : {
				'BaseClass' : GFObjects.GFSplitter,
				'Attributes' : {
					'name' : {
						'Unique' : True,
						'Typecast' : GTypecast.name,
						'Description' : 'Unique name of the tree'},
					'align': {
						'Typecast': GTypecast.name,
						'ValueSet': {
							'vertical':   {'Label': _('Vertical align')},
							'v':          {'Label': _('Vertical align')},
							'horizontal': {'Label': _('Horizontal align')},
							'h':          {'Label': _('Horizontal align')},
						},
						'Default': 'vertical',
						'Description' : 'Align'
					},
				},
				'Positionable' : True,
				'ParentTags' : ('layout','hbox','vbox','splitter','notepage','popupwindow','list'),
				'Description' : 'Mouse draggable splitter for two windows',
			},

			'options': {
				'BaseClass': GFObjects.GFOptions,
				'UsableBySiblings': True,
				'ParentTags': ('form','dialog'),
				'Label': _('Options'),
				'Description': 'TODO' },

			'option': {
				'BaseClass': GFObjects.GFOption,
				'Attributes': {
					'name': {
						'Required': True,
						'Typecast': GTypecast.name,
						'Description': 'TODO' },
					'value': {
						'Typecast': GTypecast.text,
						'Description': 'TODO' } },
				'MixedContent': True,
				'ParentTags': ('options',),
				'Label': _('Option'),
				'Description': 'TODO' },

			'title': {
				'BaseClass': GFObjects.GFOption,
				'Attributes': {
					'name': {
						'Typecast': GTypecast.name,
						'ValueSet': {
							'title': {} },
						'Default': 'title',
						'Description': 'TODO' },
					'value': {
						'Typecast': GTypecast.text,
						'Description': 'TODO' } },
				'MixedContent': True,
				'SingleInstance': True,
				'Deprecated': 'Use the <form> attribute "title" instead.',
				'ParentTags': ('options',),
				'Label': _('Form Title'),
				'Description': 'TODO' },

			'name': {
				'BaseClass': GFObjects.GFOption,
				'Attributes': {
					'name': {
						'Typecast': GTypecast.name,
						'ValueSet': {
							'name': {} },
						'Default': 'name',
						'Description': 'TODO' },
					'value': {
						'Typecast': GTypecast.text,
						'Description': 'TODO' } },
				'MixedContent': True,
				'SingleInstance': True,
				'ParentTags': ('options',),
				'Label': _('Name'),
				'Description': 'TODO' },

			'author': {
				'BaseClass': GFObjects.GFOption,
				'Attributes': {
					'name': {
						'Typecast': GTypecast.name,
						'ValueSet': {
							'author': {} },
						'Default': 'author',
						'Description': 'TODO' },
					'value': {
						'Typecast': GTypecast.text,
						'Description': 'TODO' } },
				'MixedContent': True,
				'SingleInstance': True,
				'ParentTags': ('options',),
				'Label': _('Form Author'),
				'Description': 'TODO' },

			'description':{
				'BaseClass': GFObjects.GFOption,
				'Attributes': {
					'name': {
						'Typecast': GTypecast.name,
						'ValueSet': {
							'description': {} },
						'Default': 'description',
						'Description': 'TODO' },
					'value': {
						'Typecast': GTypecast.text,
						'Description': 'TODO' } },
				'MixedContent': True,
				'SingleInstance': True,
				'ParentTags': ('options',),
				'Label': _('Description'),
				'Description': 'TODO' },

			'version': {
				'BaseClass': GFObjects.GFOption,
				'Attributes': {
					'name': {
						'Typecast': GTypecast.name,
						'ValueSet': {
							'version': {} },
						'Default': 'version',
						'Description': 'TODO' },
					'value': {
						'Typecast': GTypecast.text,
						'Description': 'TODO' } },
				'MixedContent': True,
				'SingleInstance': True,
				'ParentTags': ('options',),
				'Label': _('Version'),
				'Description': 'TODO' },

			'tip': {
				'BaseClass': GFObjects.GFOption,
				'Attributes': {
					'name': {
						'Typecast': GTypecast.name,
						'ValueSet': {
							'tip': {} },
						'Default': 'tip',
						'Description': 'TODO' },
					'value': {
						'Typecast': GTypecast.text,
						'Description': 'TODO' } },
				'MixedContent': True,
				'SingleInstance': True,
				'ParentTags': ('options',),
				'Label': _('Tip'),
				'Description': 'TODO' },
			'parameter': {
				'BaseClass': GFObjects.GFParameter,
				'Attributes': {
					'name': {
						'Label': _("Name"),
						'Description': _("Unique name of the parameter."),
						'Typecast': GTypecast.name,
						'Required': True,
						'Unique': True},
					'datatype': {
						'Label': _("Datatype"),
						'Description': _("The type of data for this parameter."),
						'Typecast': GTypecast.name,
						'ValueSet': {
							'text':     {'Label': _("Text")},
							'number':   {'Label': _('Number')},
							'date':     {'Label': _("Date")},
							'time':     {'Label': _("Time")},
							'datetime': {'Label': _("Date and time")},
							'boolean':  {'Label': _('Boolean')},
							'raw':      {'Label': _('Raw data')}},
						'Default': 'raw'},
					'length': {
						'Label': _("Length"),
						'Description': _(
							"Maximum length of data stored in this parameter. Applies "
							"only to parameters with a datatype of 'string' or "
							"'number'. For numbers, this is the total number of "
							"digits, including the fractional digits."),
						'Typecast': GTypecast.whole},
					'scale': {
						'Label': _("Scale"),
						'Description': _(
							"Number of fractional digits. Applies only to parameters "
							"with a datatype of 'number'."),
						'Typecast': GTypecast.whole},
					'required': {
						'Label': _("Required"),
						'Description': _(
							"If set, it is obligatory to provide this parameter "
							"to run the form."),
						'Typecast': GTypecast.boolean,
						'Default': False},
					'default': {
						'Label': _("Default value"),
						'Description': _(
							"Default value for the parameter, if the user does "
							"not provide a value for it."),
						'Typecast': GTypecast.text},
					'description': {
						'Label': _("Description"),
						'Description': _(
							"Description of the parameter for the help text."),
						'Typecast': GTypecast.text},
					'type': {
						'Typecast': GTypecast.name,
						'Deprecated': 'Use "datatype" instead.'}},
				'ParentTags':  ('form','dialog'),
				'Label': _('Parameter'),
				'Description': 'A form can get parameters from the outer world '
				'or a calling form, and can pass values back too '
				'in these parameters.' }}


		#
		# Create the dialog alias for the forms
		#
		copy._deepcopy_dispatch[types.FunctionType] = copy._deepcopy_atomic
		copy._deepcopy_dispatch[types.ClassType] = copy._deepcopy_atomic
		copy._deepcopy_dispatch[type(int)] = copy._deepcopy_atomic
		dialog=copy.deepcopy(xmlElements['form'])
		dialog['Required'] = False
		dialog['SingleInstance'] = False
		dialog['Importable'] = True
		dialog['Attributes']['style']['Default']='dialog'
		dialog['ParentTags']= ('form','dialog')
		dialog['Label'] = _('Dialog')

		xmlElements.update({'dialog':dialog})


		#
		# Add DataSource elements
		#
		datasourceElems = GDataSource.getXMLelements(
			updates={'datasource': {
					'BaseClass': GFObjects.GFDataSource,
					'ParentTags': ('form','dialog') },
				'cparam': {
					'BaseClass': GFObjects.GFCParam }
			})

		# TODO: This may get moved to GCommon's datasources,
		# TODO: but first have to determine if it will confuse
		# TODO: development for other tools.
		datasourceElems['datasource']['Attributes'].update( {
				'detailmin':  {
					'Label': _('M/D Min Child Rows'),
					'Description': 'If this datasource is the child in a '
					'master/detail relationship, this property '
					'specifies the minimum number of child '
					'records that must be present for a commit '
					'to be valid. Usually, this is 0 (for '
					'one-to-many relationships) or 1 '
					'(for one-to-one relationships).',
					'Default': 0,
					'Typecast': GTypecast.whole },
				'detailmax':  {
					'Label': _('M/D Max Child Rows'),
					'Description': 'If this datasource is the child in a '
					'master/detail relationship, this property '
					'specifies the maximum number of child '
					'records that can be created. Usually, this '
					'is either omitted (for one-to-many '
					'relationships) or 1 (for one-to-one '
					'relationships).',
					'Typecast': GTypecast.whole } })

		xmlElements.update( datasourceElems )

		# Add usercode elements
		xmlElements.update(usercode.get_xml_elements(
				updates = {
					'action': {'ParentTags': ('form','dialog')}
				}))

		#
		# Add trigger elements
		#
		xmlElements.update(
			GTrigger.getXMLelements(
				updates={'trigger':{
						'ParentTags': ('form','dialog')}
				}))

		xmlElements = GParser.buildImportableTags ('form', xmlElements)

	return xmlElements


#######################################################
#
# xmlFormsHandler
#
#######################################################

class xmlFormsHandler (GParser.xmlHandler):
	"""
	This class is called by the XML parser to
	process the .GFD file.
	"""
	def __init__(self):


		GParser.xmlHandler.__init__(self)

		# This is a temp thing until we figure out
		# how to better do layout namespaces
		self.xmlNamespaceAttributesAsPrefixes = True
		try:
			self.xmlElements = getXMLelements()
		except Exception, e:
			# this exception is not visible another way
			import sys
			sys.excepthook(*sys.exc_info())
