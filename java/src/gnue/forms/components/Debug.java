package gnue.forms.components;

import java.awt.*;

public class Debug {
	
	static public void dumpSizes(Component c) {
		System.out.println("Component: " + c.getClass().getName());
		System.out.println("\tMIN: " + c.getMinimumSize());
		System.out.println("\tDEF: " + c.getPreferredSize());
		System.out.println("\tMAX: " + c.getMaximumSize());
		System.out.println("\tCUR: " + c.getSize());
	}
	
}