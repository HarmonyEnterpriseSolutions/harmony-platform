package org.wonderly.swing.tabs;

import javax.swing.ImageIcon;

interface ClosableTabbedPaneUI {
	
	public void setCloseIcons( ImageIcon icon, ImageIcon downIcon );
	public void setCloseWidth( int width );
	
}
