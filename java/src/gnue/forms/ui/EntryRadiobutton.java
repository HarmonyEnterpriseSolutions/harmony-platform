package gnue.forms.ui;
import javax.swing.*;
import java.awt.event.*;


public class EntryRadiobutton extends EntryToggleButton implements ItemListener {

	/**
	 * Method EntryRadiobutton
	 *
	 *
	 */
	public EntryRadiobutton(Desktop desktop, Integer id, String label, String tip, Integer align) {
		super(desktop, id, tip, align);
		setComponent(new JRadioButton(label));
	}

	public void itemStateChanged(ItemEvent event) {
		// avoid deselect with mouse
		if (event.getStateChange() == event.SELECTED) {
			super.itemStateChanged(event);
		}
		else {
			setValue(true);
		}
	}

}

