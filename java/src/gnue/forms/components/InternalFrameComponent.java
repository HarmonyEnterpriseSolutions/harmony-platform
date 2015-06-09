package gnue.forms.components;

import javax.swing.JInternalFrame;
import javax.swing.JComponent;
import javax.swing.event.InternalFrameEvent;
import java.awt.Toolkit;
import java.awt.Rectangle;
import java.awt.Dimension;

public class InternalFrameComponent extends JInternalFrame implements FrameComponent {
	
	InternalFrameComponent(String title, boolean resizable, boolean closable, boolean maximizable, boolean iconifiable) {
		super(title, resizable, closable, maximizable, iconifiable);
	}
	
	public void postCloseEvent() {
		Toolkit.getDefaultToolkit().getSystemEventQueue().postEvent(new InternalFrameEvent(this, InternalFrameEvent.INTERNAL_FRAME_CLOSING));
	}
	
	public JComponent asComponent() {
		return this;
	}

	public void show(boolean modal, boolean maximize, boolean fit, Rectangle bounds) {
		// do not setVisible, just set bounds
		if (fit) {
			pack();
			centerOnParent();
		}
		else if (bounds != null) {
			// set delayed state bounds
			setBounds(bounds);
		}
		else if (getBounds().isEmpty()) {
			((PaneDesktopComponent)getDesktopPane()).setInternalFrameBounds(this);
		}
		if (maximize) {
			try {
				this.setMaximum(true);
			} catch (java.beans.PropertyVetoException e) {}
		}
	}
	
	public void doHide() {
		setVisible(false);
	}
		

	protected void centerOnParent() {
		// center on parent
		Dimension size = getSize();
		Dimension psize = getParent().getSize();
		
		// resize to fit parent
		size.width  = Math.min(size.width,  psize.width);
		size.height = Math.min(size.height, psize.height);
		setSize(size);
		
		setBounds((psize.width - size.width) / 2, (psize.height - size.height) / 2, size.width, size.height);
	}

    //public void restoreSubcomponentFocus() {
        //lastFocusOwner = getMostRecentFocusOwner();
        //if(lastFocusOwner == null) {
        //    lastFocusOwner = getContentPane();
        //}
        //lastFocusOwner.requestFocus();
    //}
	
}
