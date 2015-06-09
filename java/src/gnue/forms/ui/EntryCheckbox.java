package gnue.forms.ui;
import javax.swing.*;
import java.awt.event.*;


public class EntryCheckbox extends EntryToggleButton {

	/**
	 * Method EntryCheckbox
	 *
	 *
	 */
	public EntryCheckbox(Desktop desktop, Integer id, String label, String tip, Integer align) {
		super(desktop, id, tip, align);
		setComponent(new JCheckBox(label));
	}

}

