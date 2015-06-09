package gnue.forms.ui;

import gnue.forms.components.PopupControl;
import javax.swing.*;
import javax.swing.event.*;
import java.awt.*;
import java.awt.event.*;
import gnue.forms.components.TextFieldWithButtons;
import javax.swing.text.JTextComponent;

public class EntryText_with_buttons extends EntryAbstractText {

	public EntryText_with_buttons(Desktop desktop, Integer id, String label, String tip, Integer align) {
		super(desktop, id, label, tip, align);
		setComponent(new TextFieldWithButtons());
	}
	
	public JTextComponent getTextComponent() {
		return ((TextFieldWithButtons)getComponent()).getTextComponent();
	}
	
	public void uiAddWidget(Widget w) {
		((TextFieldWithButtons)getComponent()).addButton((AbstractButton)w.getComponent());
	}
	
}
