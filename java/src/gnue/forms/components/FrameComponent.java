package gnue.forms.components;

import javax.swing.JComponent;
import javax.swing.JMenuBar;
import java.awt.Rectangle;

public interface FrameComponent {

	public void postCloseEvent();
	
	public JComponent asComponent();
	
	public void show(boolean modal, boolean maximize, boolean fit, Rectangle bounds);
	public void doHide();

	// already implemented in JInternalFrame
	public void dispose();
	public void setTitle(String title);
	public void setJMenuBar(JMenuBar title);
	public Rectangle getBounds();
}
