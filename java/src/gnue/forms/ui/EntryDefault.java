package gnue.forms.ui;

import javax.swing.*;
import java.awt.*;

public class EntryDefault extends EntryAbstractText {

	public EntryDefault(Desktop desktop, Integer id, String label, String tip, Integer align) {
		super(desktop, id, label, tip, align);
		setComponent(new JTextField());
	}

}
