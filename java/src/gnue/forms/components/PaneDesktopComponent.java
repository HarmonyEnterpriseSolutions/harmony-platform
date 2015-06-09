package gnue.forms.components;

import javax.swing.*;
import java.awt.Rectangle;
import java.awt.Dimension;
import javax.swing.event.InternalFrameAdapter;
import javax.swing.event.InternalFrameEvent;

public class PaneDesktopComponent extends JDesktopPane implements DesktopComponent {
	
	Rectangle lastFrameRect = new Rectangle(0, 0, 800, 600);
	static Dimension frameShowOffset  = new Dimension(30, 30);
	
	public void setInternalFrameBounds(JInternalFrame c) {
		// set frame position with offset
		lastFrameRect.translate(frameShowOffset.height, frameShowOffset.width);
		if (lastFrameRect.y + lastFrameRect.getSize().height >= getSize().height) {
			lastFrameRect.y = frameShowOffset.height;
		}
		if (lastFrameRect.x + lastFrameRect.getSize().width >= getSize().width) {
			lastFrameRect.x = frameShowOffset.width;
		}
		c.setBounds(lastFrameRect);
	}
	
	public FrameComponent[] getAllFrameComponents() {
		JInternalFrame[] frames = getAllFrames();
		FrameComponent[] result = new FrameComponent[frames.length];
		for (int i=0; i<frames.length; i++) {
			result[i] = (FrameComponent)frames[i];
		}
		return result;
	}
	
	public JComponent asComponent() {
		return this;
	}
	
	public FrameComponent createFrameComponent(String title, boolean resizable, boolean closable, boolean maximizable, boolean iconifiable, final Runnable onClose) {
		InternalFrameComponent frame = new InternalFrameComponent(title, resizable, closable, maximizable, iconifiable);
		
		// if frame not maximizable, add it to layer 10 (like modeless dialog frame)
		// NOTE: add(Component, Object constraints) method is overrided
		add(frame, new Integer(frame.isMaximizable() ? 0 : 10));

		//need to set visible and selected because server can uiSetFocus before uiShow
		//the frame actually invisible because bounds not set
		frame.setVisible(true);
		try {
			frame.setSelected(true);
		} catch (java.beans.PropertyVetoException e) {}

		// when user pressed close frame do nothing and send onClose to server
		frame.setDefaultCloseOperation(JFrame.DO_NOTHING_ON_CLOSE);
		frame.addInternalFrameListener(new InternalFrameAdapter() {
			public void internalFrameClosing(InternalFrameEvent evt) {
				onClose.run();
			}
		});

		return frame;
	}
	
}

