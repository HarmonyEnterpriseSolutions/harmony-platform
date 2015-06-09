package gnue.forms.ui;

import javax.swing.*;
import javax.swing.event.*;
import javax.swing.text.*;
import java.awt.*;
import java.awt.event.*;
import org.json.*;
import javax.swing.plaf.basic.ComboPopup;

public class EntryDropdown extends EntryAbstractText implements ItemListener, PopupMenuListener {

	static Integer textFieldHeight = null;

	public EntryDropdown(Desktop desktop, Integer id, String label, String tip, Integer align) {
		super(desktop, id, label, tip, align);
		JComboBox combo = new JComboBox();
		combo.setEditable(true);
		setComponent(combo);
		combo.addPopupMenuListener(this);
	
		// set combobox height same as textfield
		if (textFieldHeight == null) {
			textFieldHeight = new JTextField().getPreferredSize().height;
		} 
		combo.setPreferredSize(new Dimension(combo.getPreferredSize().width, textFieldHeight));
		combo.setMinimumSize(new Dimension(combo.getMinimumSize().width, textFieldHeight));
	}

	/** == component */
	protected JComboBox getComboBox() {
		return (JComboBox)getComponent();
	}

	protected void setComponent(JComponent component) {
		super.setComponent(component);
		getComboBox().addItemListener(this);
	}

	public JTextComponent getTextComponent() {
		return (JTextComponent) getComboBox().getEditor().getEditorComponent();
	}
	
	public void uiSetEditable(Boolean editable) {
		super.uiSetEditable(editable);
		getComponent().setEnabled(editable);
	}
	

	//-------------------------------------------------------------------------
	// UI INTERFACE

	public void uiSetChoices(JSONArray choices) {
		getComboBox().removeItemListener(this);
		try {
			getComboBox().removeAllItems();
			for (int i=0; i<choices.length(); i++) {
				final String item = choices.getString(i);
				getComboBox().addItem(new Object() { public String toString() { return item; } });
			}
		}
		finally {
			getComboBox().addItemListener(this);
		}
	}

	//-------------------------------------------------------------------------
	// ItemListener
	//
	public void itemStateChanged(ItemEvent event) {
		if (event.getStateChange() == event.SELECTED) {
			//ystem.out.println(">>> ITEM STATE changed: " + event);
			SwingUtilities.invokeLater(new Runnable(){
				public void run() {
					maybeTextChanged();
				}
			});
		}
	}

	//-------------------------------------------------------------------------
	// PopupMenuListener
	//
	public void popupMenuWillBecomeVisible(PopupMenuEvent e) {
		//notify server that combobox accepted focus when mouse clicked on combobox button
		callAfter("onSetFocus");
	}
	public void popupMenuWillBecomeInvisible(PopupMenuEvent e) {
	}
	public void popupMenuCanceled(PopupMenuEvent e) {
	}

}
