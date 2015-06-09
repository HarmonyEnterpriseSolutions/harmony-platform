package gnue.forms.ui;

import gnue.forms.components.PopupControl;
import javax.swing.*;
import javax.swing.event.*;
import java.awt.*;
import java.awt.event.*;

public class EntryPicker_with_editor extends EntryPicker implements ActionListener {

	public EntryPicker_with_editor(Desktop desktop, Integer id, String label, String tip, Integer align) {
		super(desktop, id, label, tip, align);
		
		popupControl.addButton(">").addActionListener(this);
		
	}

	public void actionPerformed(ActionEvent event) {
		getTextComponent().requestFocus();
		callAfter("onCustomEditor");
	}
}
