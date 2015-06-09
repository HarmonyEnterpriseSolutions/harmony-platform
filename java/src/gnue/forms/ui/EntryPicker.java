package gnue.forms.ui;

import javax.swing.*;
import javax.swing.text.JTextComponent;
import java.awt.*;
import gnue.forms.components.PopupControl;
import org.json.*;

public class EntryPicker extends EntryAbstractText {

	protected PopupControl popupControl;

	public EntryPicker(Desktop desktop, Integer id, String label, String tip, Integer align) {
		super(desktop, id, label, tip, align);
		popupControl = new PopupControl();
		setComponent(popupControl);
	}

	public JTextComponent getTextComponent() {
		return popupControl.getTextComponent();
	}
	
	/** abstract Entry method implementation */
	public void uiSetEditable(Boolean editable) {
		super.uiSetEditable(editable);
		popupControl.setButtonsEnabled(editable);
	}
	

	//-------------------------------------------------------------------------
	// UI INTERFACE

	public void uiSetChoices(JSONArray choices) {
	}
	
	public void popdown() {
		System.out.println("POPDOWN!!!!!!!!!!!!!!!!!!!!!!!1");
		popupControl.popdown();
	}

}
