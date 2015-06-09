package gnue.forms.components;
import java.awt.*;

public class Utils {

	static public Frame getTopLevelFrame(Component comp) {
		if (comp != null) {
			for(;;) {
				comp = comp.getParent();
				if (comp == null || comp instanceof Frame)
					return (Frame)comp;
			}
		}
		return null;
	}

}
