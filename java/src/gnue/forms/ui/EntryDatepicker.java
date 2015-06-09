package gnue.forms.ui;

//import cc.gammasoft.date.*;
import com.toedter.calendar.JDateChooser;
import javax.swing.*;
import javax.swing.event.*;
import javax.swing.text.*;
import java.awt.*;
import java.awt.event.*;
import java.text.SimpleDateFormat;
import java.beans.*;

public class EntryDatepicker extends EntryAbstractText implements PropertyChangeListener, ActionListener {

	private JDateChooser dateChooser;

	public EntryDatepicker(Desktop desktop, Integer id, String label, String tip, Integer align, String format) {
		super(desktop, id, label, tip, align);
		dateChooser = new JDateChooser(null, format);
		setComponent(dateChooser);
		//dateChooser.addItemListener(this);
		//dateChooser.addPopupMenuListener(this);
		dateChooser.getDateEditor().addPropertyChangeListener("date", this);
		dateChooser.getCalendarButton().addActionListener(this);
	}

	public JTextComponent getTextComponent() {
		return (JTextComponent)dateChooser.getDateEditor();
	}

	/**
	 * date changed in dateChooser.getDateEditor()
	 * this may be as result of date choosing in popup
	 */
	public void propertyChange(PropertyChangeEvent event)  {
		maybeTextChanged();
	}

	public void actionPerformed(ActionEvent event)  {
		//callAfter("onSetFocus");
		getTextComponent().requestFocus();
	}
}
