package gnue.forms.ui;

import org.json.*;


public class EntryLabel extends EntryDefault {

	public EntryLabel(Desktop desktop, Integer id, String label, String tip, Integer align) {
		super(desktop, id, label, tip, align);
		getTextComponent().setEditable(false);
	}

	// called when picker has style label, do nothing
	public void uiSetChoices(JSONArray choices) {
	}

}
